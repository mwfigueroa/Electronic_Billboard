"""Visor animado del simulador (pygame).

Muestra el canvas cuantizado con píxeles cuadrados, reproduce la playlist en
tiempo real y permite comparar profundidades de color en vivo.

Teclas:
    SPACE       pausa
    ← / →       slide anterior / siguiente
    4 / 5 / 6   profundidad de color
    G           gamma 2.2 ↔ 1.0
    + / -       distancia simulada al cartel (±10 %; redimensiona la ventana)
    R           reinicia el slide actual
    S           captura PNG del frame actual
    Q / ESC     salir

Con ``--panel-distance`` la ventana se dimensiona para reproducir el ángulo
visual de estar a esa distancia del cartel real, según la calibración del
monitor (``--monitor-inch``, ``--monitor-px``, ``--eye-cm``). Ver
``viewing.py``.

Uso:
    python -m panel_sim.viewer examples/playlist.json
    python -m panel_sim.viewer examples/playlist.json --panel-distance 5
    python -m panel_sim.viewer examples/playlist.json --monitor-inch 27 \\
        --monitor-px 2560 --eye-cm 70 --panel-distance 5
"""

from __future__ import annotations

import argparse
import os
import signal
import socket
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from content.playlist import load
from content.timeline import Timeline

from .quantize import quantize, to_display
from .timing import refresh_hz
from .viewing import ViewingSetup

HUD_HEIGHT = 24
STARTUP_TIMEOUT_S = 20.0


def _display_reachable(display: str, timeout: float = 1.5) -> bool:
    """Prueba corta de conexión al socket de X, sin hablar protocolo."""
    try:
        spec = display.removeprefix("unix:")
        if spec.startswith(":"):
            number = int(spec[1:].split(".")[0])
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect(f"/tmp/.X11-unix/X{number}")
        else:
            host, _, rest = spec.partition(":")
            number = int(rest.split(".")[0] or "0")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, 6000 + number))
        sock.close()
        return True
    except (OSError, ValueError):
        return False


def _configure_wsl_video() -> None:
    """Ajustes para WSLg: X11 + software, y rescate del socket local.

    En WSLg conviene X11 con render por software (SDL se cuelga sin /dev/dri).
    Además, con redes en modo mirrored el ``DISPLAY`` por defecto apunta a la
    IP del host y ese camino a veces deja de responder; si pasa, se usa el
    socket local ``:0``, que es el mismo servidor. No pisa lo que el usuario
    haya definido salvo en ese rescate.
    """
    if not ("WSL_DISTRO_NAME" in os.environ or "WSL_INTEROP" in os.environ):
        return
    driver = os.environ.get("SDL_VIDEODRIVER")
    if driver is None:
        os.environ["SDL_VIDEODRIVER"] = "x11"
    os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
    if driver is not None and driver != "x11":
        return
    display = os.environ.get("DISPLAY")
    if display and not _display_reachable(display) and _display_reachable(":0"):
        print(f"aviso: DISPLAY={display} no responde; usando el socket local :0", file=sys.stderr)
        os.environ["DISPLAY"] = ":0"


def _startup_guard(ready: threading.Event) -> None:
    """Evita el cuelgue silencioso si el servidor X no responde."""
    if not ready.wait(STARTUP_TIMEOUT_S):
        print(
            f"el display no respondió en {STARTUP_TIMEOUT_S:.0f} s (¿WSLg trabado?).\n"
            "probar: `wsl --shutdown` desde Windows para reiniciar la sesión, o\n"
            "`SDL_VIDEODRIVER=dummy` para un smoke test sin ventana.",
            file=sys.stderr,
        )
        os._exit(2)


def render_surface(frame, panel_size: tuple[int, int], gap_mask, gap_cell: int):
    """Superficie de pantalla del panel: escalado + máscara de LED aplicada.

    La usan el blit del visor y la captura de la tecla S, para que lo que se
    guarda sea exactamente lo que se ve.
    """
    import pygame

    surface = pygame.image.frombuffer(
        frame.tobytes(), (frame.shape[1], frame.shape[0]), "RGB"
    )
    if gap_mask is None:
        return pygame.transform.scale(surface, panel_size)
    upscaled = pygame.transform.scale(
        surface, (frame.shape[1] * gap_cell, frame.shape[0] * gap_cell)
    )
    upscaled.blit(gap_mask, (0, 0), special_flags=pygame.BLEND_MULT)
    if upscaled.get_size() != panel_size:
        upscaled = pygame.transform.scale(upscaled, panel_size)
    return upscaled


def save_screenshot(surface, out_dir: Path) -> Path:
    import pygame

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"viewer_{datetime.now():%Y%m%d_%H%M%S}.png"
    pygame.image.save(surface, str(path))
    return path


def pixel_mask_array(width: int, height: int, cell: int, gap: int) -> np.ndarray:
    """Máscara booleana (h·cell, w·cell): True donde va el LED cuadrado.

    ``cell`` es el paso en px de pantalla y ``gap`` la máscara negra entre
    LEDs. Con ``gap`` no representable devuelve todo True (sin máscara).
    """
    if gap <= 0 or cell - gap < 1:
        return np.ones((height * cell, width * cell), dtype=bool)
    led = cell - gap
    offset = gap // 2
    ys = (np.arange(height * cell) - offset) % cell
    xs = (np.arange(width * cell) - offset) % cell
    return (ys[:, None] < led) & (xs[None, :] < led)


def pixel_dot_array(
    width: int, height: int, cell: int, gap: int, *, round_dot: bool = True
) -> np.ndarray:
    """Cobertura 0..1 del LED por píxel de pantalla (h·cell, w·cell).

    Con ``round_dot`` el LED es un círculo con el borde suavizado (la lente
    del LED real); si no, el cuadrado binario de ``pixel_mask_array``.
    """
    if gap <= 0 or cell - gap < 1:
        return np.ones((height * cell, width * cell), dtype=np.float32)
    if not round_dot:
        return pixel_mask_array(width, height, cell, gap).astype(np.float32)
    led = cell - gap
    center = (cell - 1) / 2.0
    radius = led / 2.0
    axis = np.arange(cell, dtype=np.float64) - center
    dist = np.sqrt(axis[:, None] ** 2 + axis[None, :] ** 2)
    tile = np.clip(radius + 0.5 - dist, 0.0, 1.0).astype(np.float32)
    return np.tile(tile, (height, width))


def _gap_geometry(panel_width: int, panel_px: int, gap_frac: float) -> tuple[int, int]:
    """(cell, gap) en px de pantalla; gap 0 = sin máscara representable.

    Por debajo de 5 px de celda la máscara no puede representar la proporción
    real (el LED quedaría con 1-2 px y demasiada área encendida: 37 % a celda
    3 contra el ~12 % del módulo). Tampoco baja el LED de 2 px: con 1 px el
    panel se ve más apagado que el real.
    """
    cell = panel_width // panel_px
    if gap_frac <= 0 or cell < 5:
        return cell, 0
    gap = max(1, min(round(cell * gap_frac), cell - 2))
    return cell, gap


def layout_panel(
    window_size: tuple[int, int], panel_w_px: int, panel_h_px: int, gap_frac: float
) -> tuple[tuple[int, int], int, int]:
    """Panel 2:1 centrado en la ventana, arriba del HUD.

    Con máscara activa el panel se ajusta a celdas enteras (múltiplos del
    canvas) para que el gap no se reescale y quede desparejo.
    """
    w, h = window_size
    area_h = max(1, h - HUD_HEIGHT)
    factor = min(w / panel_w_px, area_h / panel_h_px)
    panel = (max(2, round(panel_w_px * factor)), max(2, round(panel_h_px * factor)))
    cell, gap = _gap_geometry(panel[0], panel_w_px, gap_frac)
    if gap:
        panel = (cell * panel_w_px, cell * panel_h_px)
    return panel, (w - panel[0]) // 2, max(0, (area_h - panel[1]) // 2)


def run(
    playlist,
    *,
    scale: int = 5,
    depth: int | None = None,
    gamma: float | None = None,
    fps: int = 30,
    frames: int | None = None,
    out_dir: Path = Path("out"),
    clock_mhz: float = 12.5,
    start: int = 0,
    viewing: ViewingSetup | None = None,
    panel_distance_m: float | None = None,
    gap_frac: float = 0.65,
    round_led: bool = True,
) -> int:
    _configure_wsl_video()
    ready = threading.Event()
    threading.Thread(target=_startup_guard, args=(ready,), daemon=True).start()
    import pygame

    display = playlist.display
    depth = display.depth if depth is None else depth
    gamma = display.gamma if gamma is None else gamma
    viewing = viewing or ViewingSetup()
    timeline = Timeline(playlist)
    width, height = display.width, display.height
    n_slides = len(playlist.slides)

    pygame.init()
    desktop_w, desktop_h = pygame.display.get_desktop_sizes()[0]
    max_scale = max(1.0, min(desktop_w / width, desktop_h / height))
    min_distance = viewing.min_distance_m(width, height, max_scale)
    if panel_distance_m is not None and panel_distance_m < min_distance:
        print(
            f"aviso: --panel-distance {panel_distance_m:g} m no entra en pantalla "
            f"({desktop_w}×{desktop_h}); se usa {min_distance:.1f} m",
            file=sys.stderr,
        )
        panel_distance_m = min_distance
    distance_m = panel_distance_m
    panel_size = (
        viewing.window_for(width, height, distance_m)
        if distance_m is not None
        else (width * scale, height * scale)
    )
    screen = pygame.display.set_mode(
        (panel_size[0], panel_size[1] + HUD_HEIGHT), pygame.RESIZABLE
    )
    ready.set()
    pygame.display.set_caption("Simulador de panel — docs/14")
    clock = pygame.time.Clock()

    # SDL captura SIGTERM/SIGINT pero no siempre termina el loop; con estos
    # handlers la ventana se cierra limpio desde un script o un gestor.
    quit_requested = False

    def _request_quit(_signum, _frame):
        nonlocal quit_requested
        quit_requested = True

    signal.signal(signal.SIGTERM, _request_quit)
    signal.signal(signal.SIGINT, _request_quit)

    def make_hud_font(panel_width: int):
        size = min(18, max(11, (18 * (panel_width - 12)) // 360))
        return pygame.font.Font(None, size)

    def gap_for(panel_width: int):
        cell, gap = _gap_geometry(panel_width, width, gap_frac)
        if not gap:
            return None, cell, gap
        dot = pixel_dot_array(width, height, cell, gap, round_dot=round_led)
        rgb = np.repeat((dot * 255).astype(np.uint8)[:, :, None], 3, axis=2)
        return pygame.surfarray.make_surface(rgb.transpose(1, 0, 2)), cell, gap

    def layout(window_size: tuple[int, int]) -> tuple[tuple[int, int], int, int]:
        return layout_panel(window_size, width, height, gap_frac)

    def build_hud(width_px: int):
        bg = pygame.Surface((width_px, HUD_HEIGHT), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 200))
        return bg

    panel_size, panel_x, panel_y = layout(screen.get_size())
    layout_state = screen.get_size()
    layout_report_at: float | None = None
    hud_font = make_hud_font(screen.get_width())
    hud_bg = build_hud(screen.get_width())
    gap_mask, gap_cell, gap_px = gap_for(panel_size[0])

    print(
        f"calibración: monitor {viewing.monitor_inch:g}\" {viewing.aspect_label} "
        f"@{viewing.monitor_px} px · ojos a {viewing.eye_cm:g} cm · "
        f"pitch {viewing.pitch_mm:g} mm"
    )
    print(
        f"panel {panel_size[0]}×{panel_size[1]} px → como estar a "
        f"{viewing.equivalent(width, panel_size[0] / width):.1f} m del cartel real"
    )
    if gap_px:
        shape = "circular" if round_led else "cuadrado"
        print(
            f"máscara de píxel: celda {gap_cell} px · LED {shape} "
            f"{gap_cell - gap_px} px · gap {gap_px} px"
        )
    elif gap_frac <= 0:
        print("máscara de píxel: desactivada (--gap-frac 0)")
    else:
        print(
            f"máscara de píxel: no representable a {panel_size[0] / width:.1f} px/píxel "
            "(hace falta celda ≥ 5 px, subir --scale)"
        )
    if distance_m is None:
        print("(fijar la distancia del proyecto con --panel-distance 5, o +/- en vivo)")

    def set_distance(target_m: float) -> None:
        target_m = min(max(target_m, min_distance), 80.0)
        new_panel = viewing.window_for(width, height, target_m)
        if new_panel == panel_size:
            return
        pygame.display.set_mode(
            (new_panel[0], new_panel[1] + HUD_HEIGHT), pygame.RESIZABLE
        )

    index = start % n_slides
    if not timeline.slide_active(index):
        nxt = timeline.next_active(index)
        if nxt is not None:
            index = nxt
    local_t = 0.0
    paused = False
    rendered = 0
    running = True
    last_frame = None

    while running and not quit_requested:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_LEFT:
                    nxt = timeline.next_active(index, step=-1)
                    index = nxt if nxt is not None else index
                    local_t = 0.0
                elif event.key == pygame.K_RIGHT:
                    nxt = timeline.next_active(index, step=1)
                    index = nxt if nxt is not None else index
                    local_t = 0.0
                elif event.key in (pygame.K_4, pygame.K_5, pygame.K_6):
                    depth = {pygame.K_4: 4, pygame.K_5: 5, pygame.K_6: 6}[event.key]
                elif event.key == pygame.K_g:
                    gamma = 1.0 if gamma > 1.5 else 2.2
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    current = viewing.equivalent(width, panel_size[0] / width)
                    set_distance(current * 0.9)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    current = viewing.equivalent(width, panel_size[0] / width)
                    set_distance(current / 0.9)
                elif event.key == pygame.K_r:
                    local_t = 0.0
                elif event.key == pygame.K_s:
                    if last_frame is not None:
                        capture = render_surface(last_frame, panel_size, gap_mask, gap_cell)
                        print(f"captura: {save_screenshot(capture, out_dir)}")

        if screen.get_size() != layout_state:
            layout_state = screen.get_size()
            panel_size, panel_x, panel_y = layout(layout_state)
            hud_font = make_hud_font(layout_state[0])
            hud_bg = build_hud(layout_state[0])
            gap_mask, gap_cell, gap_px = gap_for(panel_size[0])
            layout_report_at = time.monotonic() + 0.5
        elif layout_report_at is not None and time.monotonic() >= layout_report_at:
            if gap_px:
                shape = "circular" if round_led else "cuadrado"
                mask_txt = f"LED {shape} {gap_cell - gap_px} px · gap {gap_px} px"
            else:
                mask_txt = "sin máscara (celda < 5 px)"
            print(
                f"ventana {layout_state[0]}×{layout_state[1]} → panel "
                f"{panel_size[0]}×{panel_size[1]} px · {mask_txt} · "
                f"~{viewing.equivalent(width, panel_size[0] / width):.1f} m reales"
            )
            layout_report_at = None

        dt = clock.tick(fps) / 1000.0
        now = datetime.now()
        if not paused:
            local_t += dt
            while local_t >= playlist.slides[index].duration:
                local_t -= playlist.slides[index].duration
                nxt = timeline.next_active(index, now)
                if nxt is not None:
                    index = nxt
        # si se cerró la ventana horaria del slide actual, pasar al siguiente
        if not timeline.slide_active(index, now):
            nxt = timeline.next_active(index, now)
            if nxt is not None:
                index, local_t = nxt, 0.0

        if timeline.slide_active(index, now):
            frame = timeline.frame_at(index, local_t, now=now)
        else:
            frame = np.zeros((height, width, 3), dtype=np.uint8)   # sin programa
        last_frame = to_display(quantize(frame, depth, gamma), depth)
        scaled = render_surface(last_frame, panel_size, gap_mask, gap_cell)
        screen.blit(scaled, (panel_x, panel_y))

        current_scale = panel_size[0] / width
        hud = (
            f"{index + 1}/{n_slides} · {depth}b · gamma {gamma:g} · "
            f"{refresh_hz(clock_mhz * 1e6, depth):.0f}Hz · "
            f"~{viewing.equivalent(width, current_scale):.1f}m · "
            f"{'SIN HORARIO · ' if not timeline.slide_active(index, now) else ''}"
            f"{'PAUSA · ' if paused else ''}SPACE ←→ 456 G +/- R S Q"
        )
        hud_y = screen.get_height() - HUD_HEIGHT
        screen.blit(hud_bg, (0, hud_y))
        screen.blit(hud_font.render(hud, True, (220, 220, 220)), (6, hud_y + 3))
        pygame.display.flip()

        rendered += 1
        if frames is not None and rendered >= frames:
            running = False

    pygame.quit()
    timeline.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="panel_sim.viewer",
        description="Visor animado del simulador de panel.",
    )
    parser.add_argument("playlist", type=Path)
    parser.add_argument("--scale", type=int, default=5, help="factor de ampliación inicial (modo manual)")
    parser.add_argument("--depth", type=int, default=None, help="bits por color (4, 5, 6)")
    parser.add_argument("--gamma", type=float, default=None, help="exponente de gamma (1 = sin corrección)")
    parser.add_argument("--fps", type=int, default=30, help="frames por segundo de la animación")
    parser.add_argument("--frames", type=int, default=None, help="salir tras N frames (smoke test)")
    parser.add_argument("--start", type=int, default=0, help="slide inicial (0-based)")
    parser.add_argument("--out", type=Path, default=Path("out"), help="directorio de capturas (tecla S)")
    parser.add_argument("--clock-mhz", type=float, default=12.5, help="clock de panel para el cálculo de refresco")
    parser.add_argument("--panel-distance", type=float, default=None,
                        help="emular esta distancia al cartel real, en metros (p. ej. 5)")
    parser.add_argument("--pitch-mm", type=float, default=5.0, help="paso de píxel del panel (P5 → 5 mm)")
    parser.add_argument("--monitor-inch", type=float, default=24.0, help="diagonal de tu monitor, pulgadas")
    parser.add_argument("--monitor-px", type=int, default=1920, help="ancho de tu monitor, píxeles")
    parser.add_argument("--monitor-aspect", type=str, default="16:9", help="aspecto de tu monitor, W:H")
    parser.add_argument("--eye-cm", type=float, default=60.0, help="tu distancia normal a la pantalla, cm")
    parser.add_argument("--gap-frac", type=float, default=0.65,
                        help="fracción del paso de píxel que ocupa la máscara negra (0 = sin máscara)")
    parser.add_argument("--led-shape", choices=("round", "square"), default="round",
                        help="forma del LED en la máscara (round = circular suavizado, como el real)")
    args = parser.parse_args(argv)

    playlist = load(args.playlist)
    if not 0 <= args.start < len(playlist.slides):
        parser.error(f"--start fuera de rango: {args.start} (0..{len(playlist.slides) - 1})")
    if not 0.0 <= args.gap_frac < 1.0:
        parser.error("--gap-frac debe estar entre 0 y 1")
    try:
        aw, ah = (int(part) for part in args.monitor_aspect.split(":"))
        if aw <= 0 or ah <= 0:
            raise ValueError
    except ValueError:
        parser.error("--monitor-aspect debe ser W:H, p. ej. 16:9")
    viewing = ViewingSetup(
        pitch_mm=args.pitch_mm, monitor_inch=args.monitor_inch, monitor_px=args.monitor_px,
        aspect=(aw, ah), eye_cm=args.eye_cm,
    )
    return run(
        playlist,
        scale=max(1, args.scale), depth=args.depth, gamma=args.gamma,
        fps=args.fps, frames=args.frames, out_dir=args.out, clock_mhz=args.clock_mhz,
        start=args.start, viewing=viewing, panel_distance_m=args.panel_distance,
        gap_frac=args.gap_frac, round_led=args.led_shape == "round",
    )


if __name__ == "__main__":
    raise SystemExit(main())
