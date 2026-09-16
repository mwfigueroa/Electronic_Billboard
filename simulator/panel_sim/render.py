"""Render PNG: cada slide cuantizado, ampliado con píxeles cuadrados visibles.

Uso:
    python -m panel_sim.render examples/playlist.json -o out
    python -m panel_sim.render examples/playlist.json --slide 2 --depth 4 --time 21:45:00
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from PIL import Image

from content.canvas import scale_with_grid
from content.playlist import load
from content.timeline import Timeline

from .quantize import quantize, to_display
from .timing import refresh_hz

TIME_FORMATS = ("%H:%M:%S", "%Y-%m-%d %H:%M:%S")


def parse_time(value: str) -> datetime:
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise SystemExit(f"--time inválido: {value!r} (usar HH:MM:SS)")


def render(
    playlist_path: str | Path,
    out_dir: str | Path,
    *,
    scale: int = 4,
    grid: bool = True,
    depth: int | None = None,
    gamma: float | None = None,
    slide_index: int | None = None,
    now: datetime | None = None,
) -> tuple[list[Path], int, float]:
    """Renderiza los slides a PNG. Devuelve (rutas, profundidad, gamma)."""
    playlist = load(playlist_path)
    depth = playlist.display.depth if depth is None else depth
    gamma = playlist.display.gamma if gamma is None else gamma
    now = now or datetime.now()
    timeline = Timeline(playlist)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for index, slide in enumerate(playlist.slides):
        if slide_index is not None and index != slide_index:
            continue
        frame = timeline.frame_at(index, 0.0, now=now)
        display_frame = to_display(quantize(frame, depth, gamma), depth)
        img = Image.fromarray(display_frame)
        if scale > 1:
            img = scale_with_grid(img, scale) if grid else img.resize(
                (img.width * scale, img.height * scale), Image.NEAREST
            )
        path = out_dir / f"{index:02d}_{slide.type}.png"
        img.save(path)
        written.append(path)
        print(f"[{index:02d}] {slide.type:<5} {slide.duration:5.1f}s → {path}")
    timeline.close()
    return written, depth, gamma


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="panel_sim.render",
        description="Renderiza una playlist a PNG con píxeles cuadrados visibles.",
    )
    parser.add_argument("playlist", type=Path)
    parser.add_argument("-o", "--out", type=Path, default=Path("out"))
    parser.add_argument("--slide", type=int, default=None, help="renderizar solo el slide N (0-based)")
    parser.add_argument("--scale", type=int, default=4, help="factor de ampliación (1 = tamaño real)")
    parser.add_argument("--no-grid", action="store_true", help="sin grilla entre píxeles")
    parser.add_argument("--depth", type=int, default=None, help="bits por color (4, 5, 6)")
    parser.add_argument("--gamma", type=float, default=None, help="exponente de gamma (1 = sin corrección)")
    parser.add_argument("--time", type=str, default=None, help="hora fija HH:MM:SS para los slides de reloj")
    args = parser.parse_args(argv)

    playlist = load(args.playlist)
    now = parse_time(args.time) if args.time else datetime.now()
    written, depth, gamma = render(
        args.playlist, args.out,
        scale=max(1, args.scale), grid=not args.no_grid,
        depth=args.depth, gamma=args.gamma, slide_index=args.slide, now=now,
    )

    display = playlist.display
    print(
        f"\n{len(written)} slide(s) · canvas {display.width}×{display.height} · "
        f"{depth} bits/color · gamma {gamma:g}"
    )
    for mega in (12.5, 25.0):
        print(f"refresco BCM estimado @ {mega:g} MHz: {refresh_hz(mega * 1e6, depth):.0f} Hz")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
