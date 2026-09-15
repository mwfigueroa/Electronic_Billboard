"""Primitivas de imagen del canvas RGB888.

La composición usa Pillow (RGB/RGBA); la cuantización y los bitplanes trabajan
sobre numpy en `quantize` y `bitplanes`.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

_FONT_DIRS = (Path("/usr/share/fonts/truetype/dejavu"), Path("/usr/share/fonts"))

_FONT_FILES = {
    "DejaVuSans": "DejaVuSans.ttf",
    "DejaVuSans-Bold": "DejaVuSans-Bold.ttf",
    "DejaVuSansMono": "DejaVuSansMono.ttf",
    "DejaVuSansMono-Bold": "DejaVuSansMono-Bold.ttf",
    "DejaVuSerif": "DejaVuSerif.ttf",
    "DejaVuSerif-Bold": "DejaVuSerif-Bold.ttf",
}


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    """``#rgb`` o ``#rrggbb`` → tupla RGB."""
    s = value.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        raise ValueError(f"color inválido: {value!r} (se espera #rrggbb o #rgb)")
    try:
        r, g, b = (int(s[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        raise ValueError(f"color inválido: {value!r}") from None
    return r, g, b


def resolve_font(name: str) -> Path:
    """Familia conocida de DejaVu o ruta directa a un .ttf/.otf."""
    direct = Path(name)
    is_file = direct.suffix.lower() in {".ttf", ".otf"} and direct.exists()
    if is_file:
        return direct
    filename = _FONT_FILES.get(name)
    if filename is None and direct.suffix.lower() in {".ttf", ".otf"}:
        filename = name
    if filename:
        for directory in _FONT_DIRS:
            candidate = directory / filename
            if candidate.exists():
                return candidate
    conocidas = ", ".join(sorted(_FONT_FILES))
    raise FileNotFoundError(
        f"fuente {name!r} no encontrada; usar una ruta .ttf o una de: {conocidas}"
    )


def new_canvas(width: int, height: int, background: tuple[int, int, int]) -> Image.Image:
    return Image.new("RGB", (width, height), background)


def text_image(
    text: str,
    font_name: str,
    size: int,
    color: tuple[int, int, int],
    *,
    align: str = "left",
) -> Image.Image:
    """Texto (multi-línea con ``\\n``) sobre fondo transparente, RGBA."""
    font = ImageFont.truetype(str(resolve_font(font_name)), size)
    lines = text.split("\n")
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    widths = [probe.textlength(line, font=font) for line in lines]
    ascent, descent = font.getmetrics()
    line_h = ascent + descent
    width = max(1, int(np.ceil(max(widths))))
    height = max(1, line_h * len(lines))
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        if align == "center":
            x = (width - widths[i]) / 2
        elif align == "right":
            x = width - widths[i]
        else:
            x = 0
        draw.text((x, i * line_h), line, font=font, fill=(*color, 255))
    return img


def contain(img: Image.Image, width: int, height: int, *, limit_width: bool = True) -> Image.Image:
    """Escala hacia abajo para entrar en el canvas; nunca agranda.

    ``limit_width=False`` limita solo por altura: es lo que necesita una
    imagen que se va a desplazar, para conservar su ancho y tener algo que
    desplazar.
    """
    scale_x = width / img.width if limit_width else 1.0
    scale = min(scale_x, height / img.height, 1.0)
    if scale >= 1.0:
        return img
    size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    return img.resize(size, Image.LANCZOS)


def paste_aligned(
    canvas: Image.Image,
    img: Image.Image,
    align: str = "center",
    valign: str = "middle",
    margin: int = 0,
) -> None:
    x = {
        "left": margin,
        "center": (canvas.width - img.width) // 2,
        "right": canvas.width - img.width - margin,
    }[align]
    y = {
        "top": margin,
        "middle": (canvas.height - img.height) // 2,
        "bottom": canvas.height - img.height - margin,
    }[valign]
    canvas.paste(img, (x, y), img)


def scale_with_grid(img: Image.Image, scale: int, grid_color: tuple[int, int, int] = (24, 24, 24)) -> Image.Image:
    """Amplía a píxeles cuadrados visibles: vecino más próximo + grilla."""
    if scale <= 1:
        return img
    big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    draw = ImageDraw.Draw(big)
    for x in range(1, img.width):
        draw.line(((x * scale - 1, 0), (x * scale - 1, big.height - 1)), fill=grid_color)
    for y in range(1, img.height):
        draw.line(((0, y * scale - 1), (big.width - 1, y * scale - 1)), fill=grid_color)
    return big
