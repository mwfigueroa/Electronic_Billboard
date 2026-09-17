"""Clips de ejemplo generados (256×128, deterministas).

Dos placas de 10 s para probar el slide ``video`` (y la fidelidad del vínculo
directo, que las muestra sin códec de por medio). Los cuadros se dibujan con
Pillow, deterministas respecto de ``t``, y ffmpeg solo codifica:

- ``pauta``: tanda publicitaria — "GRAN OFERTA", "2x1 HOY" y "LLAMÁ YA" con
  zoom, entrada lateral, parpadeo y una marquesina que corre abajo.
- ``ia``: placa de inteligencia artificial — red neuronal con pulsos viajando
  por las sinapsis y el texto "Powered by DeepSeek".

Uso:
    python -m content.clips              # ambos en examples/videos/
    python -m content.clips ia           # solo uno
    make clips
"""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Callable
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .canvas import resolve_font
from .video import ffmpeg_exe

WIDTH, HEIGHT = 256, 128
FPS = 25.0
DURATION = 10.0
FONT_NAME = "DejaVuSans-Bold"
MARQUEE_TEXT = "★ CARTEL LED P5 ★ TU MARCA ACÁ ★ LLAMÁ YA ★ "
MARQUEE_H = 22
MARQUEE_SPEED = 90.0   # px/s
MAX_TEXT_WIDTH = WIDTH - 32

_fonts: dict[int, ImageFont.FreeTypeFont] = {}


def _font(size: int) -> ImageFont.FreeTypeFont:
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(str(resolve_font(FONT_NAME)), size)
    return _fonts[size]


def _text_image(
    text: str, size: int, color: tuple[int, int, int],
    *, stroke: tuple[int, int, int] = (0, 0, 0), stroke_width: int = 2,
    max_width: int | None = MAX_TEXT_WIDTH,
) -> Image.Image:
    """Texto RGBA con contorno: legible sobre cualquier fondo.

    Con ``max_width`` el tamaño se reduce solo para que nunca se salga del
    panel (los textos de escena; la marquesina va sin tope).
    """
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    def box(font):
        return probe.textbbox((0, 0), text, font=font, stroke_width=stroke_width)

    font = _font(size)
    left, top, right, bottom = box(font)
    if max_width is not None and right - left > max_width:
        size = max(8, int(size * max_width / (right - left)))
        font = _font(size)
        left, top, right, bottom = box(font)
    img = Image.new("RGBA", (right - left, bottom - top), (0, 0, 0, 0))
    ImageDraw.Draw(img).text(
        (-left, -top), text, font=font, fill=color + (255,),
        stroke_width=stroke_width, stroke_fill=stroke + (255,),
    )
    return img


def _set_alpha(img: Image.Image, factor: float) -> None:
    """Atenúa el texto (apariciones y pulsos)."""
    img.putalpha(img.getchannel("A").point(lambda value: int(value * factor)))


def _stripes(offset: int, dark: tuple[int, int, int], light: tuple[int, int, int]) -> Image.Image:
    """Fondo de franjas diagonales desplazadas: el fondo 'en acción'."""
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
    band = ((xx + yy + offset) // 16) % 2
    array = np.where(
        band[..., None] == 0,
        np.array(dark, dtype=np.uint8),
        np.array(light, dtype=np.uint8),
    )
    return Image.fromarray(array.astype(np.uint8)).convert("RGBA")


# --- pauta publicitaria ------------------------------------------------------

_MARQUEE: Image.Image | None = None


def _draw_marquee(canvas: Image.Image, t: float) -> None:
    global _MARQUEE
    if _MARQUEE is None:
        _MARQUEE = _text_image(MARQUEE_TEXT, 16, (255, 255, 255),
                               stroke_width=1, max_width=None)
    canvas.alpha_composite(
        Image.new("RGBA", (WIDTH, MARQUEE_H), (0, 0, 0, 150)),
        (0, HEIGHT - MARQUEE_H),
    )
    strip = _MARQUEE
    x = -(int(t * MARQUEE_SPEED) % strip.width)
    while x < WIDTH:
        canvas.paste(strip, (x, HEIGHT - MARQUEE_H), strip)
        x += strip.width


def pauta_frame_at(t: float) -> np.ndarray:
    """Cuadro de la pauta en el segundo ``t`` (función pura, testeable)."""
    if t < 3.5:
        # escena 1: "GRAN OFERTA" entra con zoom sobre franjas rojas
        canvas = _stripes(int(t * 70), (150, 24, 24), (96, 12, 12))
        grow = min(t / 0.7, 1.0)
        img = _text_image("GRAN OFERTA", int(16 + 17 * grow), (255, 224, 64))
        canvas.alpha_composite(img, ((WIDTH - img.width) // 2,
                                     (HEIGHT - MARQUEE_H - img.height) // 2))
    elif t < 7.0:
        # escena 2: "2x1 HOY" entra desde la derecha sobre azules
        canvas = _stripes(-int(t * 130), (16, 48, 128), (8, 24, 72))
        settle = 1 - (1 - min((t - 3.5) / 0.8, 1.0)) ** 3
        img = _text_image("2x1 HOY", 44, (255, 255, 255))
        center = WIDTH // 2 - img.width // 2
        x = int(WIDTH + (center - WIDTH) * settle)
        canvas.alpha_composite(img, (x, (HEIGHT - MARQUEE_H - img.height) // 2))
    else:
        # escena 3: "LLAMÁ YA" parpadea sobre rojo pulsante y aparece el teléfono
        pulse = 40 + int(60 * abs(np.sin(t * 6)))
        canvas = Image.new("RGBA", (WIDTH, HEIGHT), (pulse, 8, 8, 255))
        if (t * 2) % 1.0 < 0.65:
            img = _text_image("LLAMÁ YA", 44, (255, 255, 255))
            canvas.alpha_composite(img, ((WIDTH - img.width) // 2, 12))
        if t - 7.0 > 0.6:
            phone = _text_image("011 5555 0123", 20, (255, 224, 64))
            canvas.alpha_composite(
                phone, ((WIDTH - phone.width) // 2, HEIGHT - MARQUEE_H - phone.height - 4)
            )
    _draw_marquee(canvas, t)
    return np.asarray(canvas.convert("RGB"), dtype=np.uint8)


# --- placa de inteligencia artificial ----------------------------------------

NET_LAYERS = (4, 6, 4)


def _net_nodes() -> list[list[tuple[float, float]]]:
    columns = (44.0, WIDTH / 2, WIDTH - 44.0)
    nodes = []
    for x, count in zip(columns, NET_LAYERS):
        nodes.append([
            (x, HEIGHT / 2 + (index - (count - 1) / 2) * 16.0)
            for index in range(count)
        ])
    return nodes


_NODES = _net_nodes()
_EDGES = [
    ((x1, y1), (x2, y2))
    for layer_a, layer_b in zip(_NODES, _NODES[1:])
    for (x1, y1) in layer_a
    for (x2, y2) in layer_b
]


def ia_frame_at(t: float) -> np.ndarray:
    """Cuadro de la placa de IA en el segundo ``t`` (función pura, testeable)."""
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (6, 10, 24, 255))
    draw = ImageDraw.Draw(canvas)
    for k in range(10):   # datos de fondo cayendo: textura en movimiento
        x = 14 + k * 25
        y = int(t * 42 + k * 37) % (HEIGHT + 16) - 8
        draw.line((x, y, x, y + 5), fill=(24, 44, 84, 255), width=1)
    for (x1, y1), (x2, y2) in _EDGES:   # sinapsis
        draw.line((x1, y1, x2, y2), fill=(26, 52, 96, 255), width=1)
    for index, ((x1, y1), (x2, y2)) in enumerate(_EDGES):   # pulsos viajando
        phase = (t * 0.7 + index * 0.137) % 1.0
        x = x1 + (x2 - x1) * phase
        y = y1 + (y2 - y1) * phase
        draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(80, 220, 255, 255))
    for layer in _NODES:   # neuronas
        for (x, y) in layer:
            draw.ellipse((x - 4, y - 4, x + 4, y + 4),
                         fill=(16, 34, 64, 255), outline=(70, 150, 230, 255), width=1)

    if t < 5.0:
        title = _text_image("IA", 96, (255, 255, 255), stroke_width=3)
        canvas.alpha_composite(title, ((WIDTH - title.width) // 2, 6))
        subtitle = _text_image("INTELIGENCIA ARTIFICIAL", 15, (140, 220, 255))
        canvas.alpha_composite(subtitle, ((WIDTH - subtitle.width) // 2,
                                          HEIGHT - subtitle.height - 8))
    else:
        fade = min((t - 5.0) / 0.4, 1.0)
        pulse = 0.85 + 0.15 * float(np.sin(t * 6))
        top = _text_image("Powered by", 18, (235, 235, 235))
        brand = _text_image("DeepSeek", 44, (90, 200, 255), stroke_width=3)
        _set_alpha(top, fade)
        _set_alpha(brand, fade * pulse)
        total = top.height + 4 + brand.height
        y0 = (HEIGHT - total) // 2
        canvas.alpha_composite(top, ((WIDTH - top.width) // 2, y0))
        canvas.alpha_composite(brand, ((WIDTH - brand.width) // 2, y0 + top.height + 4))
    return np.asarray(canvas.convert("RGB"), dtype=np.uint8)


CLIPS: dict[str, Callable[[float], np.ndarray]] = {
    "pauta": pauta_frame_at,
    "ia": ia_frame_at,
}


def frame_at(t: float, clip: str = "pauta") -> np.ndarray:
    """Cuadro del clip ``clip`` en el segundo ``t``."""
    return CLIPS[clip](t)


def write_clip(
    path: str | Path, clip: str = "pauta", *, fps: float = FPS, duration: float = DURATION
) -> Path:
    """Codifica un clip a mp4 (H.264) con ffmpeg."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = round(duration * fps)
    command = [
        ffmpeg_exe(), "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
        "-r", f"{fps:g}", "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        "-movflags", "+faststart", str(path),
    ]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as proc:
        assert proc.stdin is not None
        for index in range(count):
            proc.stdin.write(frame_at(index / fps, clip).tobytes())
        proc.stdin.close()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg terminó con código {proc.returncode}")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="content.clips",
        description="Genera los clips de ejemplo (256×128, sin red).",
    )
    parser.add_argument("clips", nargs="*", choices=sorted(CLIPS),
                        help="cuáles generar (por defecto, todos)")
    parser.add_argument("--out-dir", type=Path, default=Path("examples/videos"))
    args = parser.parse_args(argv)
    for name in args.clips or sorted(CLIPS):
        path = write_clip(args.out_dir / f"{name}.mp4", name)
        print(f"clip: {path} · {round(DURATION * FPS)} cuadros · {DURATION:g} s @ {FPS:g} fps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
