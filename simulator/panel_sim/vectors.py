"""Vectores dorados para los testbenches del HDL.

Emite, a partir de un patrón canónico (gradiente R horizontal, gradiente G
vertical, damero B):

- ``frame_rgb888.mem``: el frame de entrada, un píxel por línea (``rrggbb``).
- ``gamma_lut_*.mem``: la LUT de gamma + cuantización (256 entradas), generada
  con ``quantize`` para que el HDL coincida bit a bit con el software.
- ``bitplane_b*_{r,g,b}.mem``: los 15 planos esperados, ``$readmemh`` con una
  línea por fila ``y`` y un dígito hex cada 4 píxeles (``x=0`` = LSB).
- ``expected_levels.json`` y ``manifest.json``: niveles por canal y layout.

El layout es el canónico pre-mapeo de ``bitplanes``: el testbench del HDL
aplica después el mismo mapeo de scan que el diseño, igual que en el panel.

Uso:
    python -m panel_sim.vectors -o vectors
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .bitplanes import canonical_test_frame, rgb_to_bitplanes
from .quantize import quantize


def lut_name(gamma: float, depth: int) -> str:
    gamma_tag = f"{gamma:g}".replace(".", "p")
    return f"gamma_lut_{gamma_tag}_{depth}b.mem"


def write_gamma_lut(out_dir: str | Path, *, depth: int = 5, gamma: float = 2.2) -> Path:
    """LUT de 256 entradas para el HDL, calculada con ``quantize``.

    El HDL que la use reproduce la gamma y la cuantización del software de
    forma exacta (mismo redondeo incluido).
    """
    out_dir = Path(out_dir)
    ramp = np.arange(256, dtype=np.uint8).reshape(256, 1, 1).repeat(3, axis=2)
    levels = quantize(ramp, depth, gamma)[:, 0, 0]
    path = out_dir / lut_name(gamma, depth)
    path.write_text("\n".join(f"{int(v):02x}" for v in levels) + "\n", encoding="ascii")
    return path


def _frame_lines(frame: np.ndarray) -> list[str]:
    lines = []
    for y in range(frame.shape[0]):
        for x in range(frame.shape[1]):
            r, g, b = frame[y, x]
            lines.append(f"{int(r):02x}{int(g):02x}{int(b):02x}")
    return lines


def write_vectors(
    out_dir: str | Path,
    *,
    width: int = 16,
    height: int = 8,
    depth: int = 5,
    gamma: float = 2.2,
) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    frame = canonical_test_frame(width, height)
    levels = quantize(frame, depth, gamma)
    planes = rgb_to_bitplanes(levels, depth)

    digits = (width + 3) // 4
    files: dict[str, str] = {}
    written: list[Path] = []
    for bit in range(depth):
        for channel, name in enumerate("rgb"):
            rows = []
            for y in range(height):
                value = 0
                for x in range(width):
                    value |= int(planes[bit, channel, y, x]) << x
                rows.append(f"{value:0{digits}x}")
            path = out_dir / f"bitplane_b{bit}_{name}.mem"
            path.write_text("\n".join(rows) + "\n", encoding="ascii")
            files[f"b{bit}_{name}"] = path.name
            written.append(path)

    manifest = {
        "format": "readmemh",
        "width": width,
        "height": height,
        "depth": depth,
        "gamma": gamma,
        "pattern": "R = x·255/(w−1), G = y·255/(h−1), B = 255 si (x+y) es impar, 0 si es par",
        "layout": "planes[bit][canal][y][x]; bit 0 = LSB; x=0 = izquierda del canvas",
        "mem_layout": "una línea por y; dígito hex por cada 4 px; x=0 = bit menos significativo",
        "frame": {
            "file": "frame_rgb888.mem",
            "layout": "un píxel por línea (rrggbb), orden y y luego x",
        },
        "gamma_lut": {
            "file": lut_name(gamma, depth),
            "layout": "256 niveles, uno por línea, índice = valor sRGB 0..255",
            "note": "generada con quantize(); el HDL debe devolver el mismo nivel",
        },
        "files": files,
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    written.append(manifest_path)

    levels_path = out_dir / "expected_levels.json"
    levels_path.write_text(
        json.dumps(
            {
                "width": width,
                "height": height,
                "depth": depth,
                "gamma": gamma,
                "r": levels[:, :, 0].tolist(),
                "g": levels[:, :, 1].tolist(),
                "b": levels[:, :, 2].tolist(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(levels_path)

    frame_path = out_dir / "frame_rgb888.mem"
    frame_path.write_text("\n".join(_frame_lines(frame)) + "\n", encoding="ascii")
    written.append(frame_path)

    lut_path = write_gamma_lut(out_dir, depth=depth, gamma=gamma)
    written.append(lut_path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="panel_sim.vectors",
        description="Genera vectores dorados de bitplanes para testbenches.",
    )
    parser.add_argument("-o", "--out", type=Path, default=Path("vectors"))
    parser.add_argument("--width", type=int, default=16)
    parser.add_argument("--height", type=int, default=8)
    parser.add_argument("--depth", type=int, default=5)
    parser.add_argument("--gamma", type=float, default=2.2)
    args = parser.parse_args(argv)

    written = write_vectors(
        args.out, width=args.width, height=args.height,
        depth=args.depth, gamma=args.gamma,
    )
    print(f"{len(written)} archivos en {args.out}/ ({args.width}×{args.height}, {args.depth} bits)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
