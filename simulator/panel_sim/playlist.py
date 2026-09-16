"""Playlist declarativa: carga, validación y modelo.

Formato JSON. Cada slide tiene un ``type`` y una ``duration`` en segundos; el
resto de los campos depende del tipo. Las claves desconocidas son un error:
un typo como ``"duraton"`` se detecta al cargar, no al renderizar.

Tipos soportados:

- ``text``  — texto estático o desplazándose.
- ``image`` — imagen (PNG/JPG), contenida dentro del canvas.
- ``video`` — video (MP4/WebM), decodificado con ffmpeg (ver ``video.py``).
- ``live``  — fuente viva por red o X11 (contrato de wire v1, docs/14):
  frames RGB888 de 256×128 por UDP, MJPEG/HTTP o ``x11grab``.
- ``clock`` — reloj local; se re-renderiza en cada frame del visor.
- ``color`` — color plano.

Especificación: docs/14_software_contenido.md.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from .canvas import hex_to_rgb

DEFAULT_FONT = "DejaVuSans-Bold"


class PlaylistError(ValueError):
    """Playlist inválida; el mensaje indica el campo y el motivo."""


@dataclass(frozen=True)
class Display:
    width: int = 256
    height: int = 128
    depth: int = 5
    gamma: float = 2.2
    background: str = "#000000"


@dataclass(frozen=True)
class TextSlide:
    type: ClassVar[str] = "text"
    duration: float
    text: str
    size: int = 16
    color: str = "#ffffff"
    background: str | None = None
    font: str = DEFAULT_FONT
    align: str = "center"
    valign: str = "middle"
    scroll: str | None = None
    speed_px_s: float = 20.0


@dataclass(frozen=True)
class ImageSlide:
    type: ClassVar[str] = "image"
    duration: float
    path: Path
    background: str | None = None
    scroll: str | None = None
    speed_px_s: float = 20.0


@dataclass(frozen=True)
class VideoSlide:
    type: ClassVar[str] = "video"
    duration: float
    path: Path
    loop: bool = True
    fps: float = 30.0


LIVE_FORMATS = (None, "rawvideo", "x11grab", "v4l2", "mjpeg")


@dataclass(frozen=True)
class LiveSlide:
    """Fuente viva (contrato de wire v1, docs/14).

    ``url`` es la entrada de ffmpeg: ``udp://host:puerto``,
    ``http://host/stream.mjpg`` o el display para ``x11grab`` (``:0.0+0,0``).
    ``size`` es el tamaño de la fuente para ``rawvideo`` (``"256x128"``).
    """

    type: ClassVar[str] = "live"
    duration: float
    url: str
    fps: float = 30.0
    format: str | None = None
    pixel_format: str | None = None
    size: str | None = None

    @property
    def input_args(self) -> tuple[str, ...]:
        args: list[str] = []
        if self.format:
            args += ["-f", self.format]
        if self.format == "rawvideo":
            args += ["-pixel_format", self.pixel_format or "rgb24"]
        if self.size:
            args += ["-video_size", self.size]
        if self.format in ("x11grab", "v4l2"):
            args += ["-framerate", f"{self.fps:g}"]
        return tuple(args)


@dataclass(frozen=True)
class ClockSlide:
    type: ClassVar[str] = "clock"
    duration: float
    fmt: str = "%H:%M:%S"
    size: int = 16
    color: str = "#ffffff"
    background: str | None = None
    font: str = DEFAULT_FONT


@dataclass(frozen=True)
class ColorSlide:
    type: ClassVar[str] = "color"
    duration: float
    color: str


Slide = TextSlide | ImageSlide | VideoSlide | LiveSlide | ClockSlide | ColorSlide


@dataclass(frozen=True)
class Playlist:
    display: Display
    slides: tuple[Slide, ...]
    source: Path
    version: int = 1

    @property
    def duration(self) -> float:
        return sum(slide.duration for slide in self.slides)


def load(path: str | Path) -> Playlist:
    """Lee y valida una playlist desde un archivo JSON."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise PlaylistError(f"no existe la playlist: {path}") from None
    except json.JSONDecodeError as exc:
        raise PlaylistError(f"JSON inválido en {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise PlaylistError("la playlist debe ser un objeto JSON")
    _check_keys(raw, {"version", "display", "slides"}, "playlist")

    version = raw.get("version", 1)
    if not isinstance(version, int) or isinstance(version, bool):
        raise PlaylistError("'version' debe ser entero")

    display = _parse_display(raw.get("display", {}))
    slides_raw = raw.get("slides")
    if not isinstance(slides_raw, list) or not slides_raw:
        raise PlaylistError("'slides' debe ser una lista no vacía")
    slides = tuple(
        _parse_slide(item, path.parent, index)
        for index, item in enumerate(slides_raw)
    )
    return Playlist(display=display, slides=slides, source=path, version=version)


def _check_keys(raw: dict, allowed: set[str], ctx: str) -> None:
    extra = set(raw) - allowed
    if extra:
        raise PlaylistError(f"{ctx}: claves desconocidas: {', '.join(sorted(extra))}")


def _parse_display(raw: Any) -> Display:
    if not isinstance(raw, dict):
        raise PlaylistError("'display' debe ser un objeto")
    _check_keys(raw, {"width", "height", "depth", "gamma", "background"}, "display")
    width = _integer(raw, "width", 256, "display", positive=True)
    height = _integer(raw, "height", 128, "display", positive=True)
    depth = _integer(raw, "depth", 5, "display", positive=True)
    if not 1 <= depth <= 8:
        raise PlaylistError("display: 'depth' debe estar entre 1 y 8")
    gamma = _number(raw, "gamma", 2.2, "display", positive=True)
    background = _validate_color(raw.get("background", "#000000"), "display")
    return Display(width=width, height=height, depth=depth, gamma=gamma, background=background)


def _parse_slide(raw: Any, base: Path, index: int) -> Slide:
    if not isinstance(raw, dict):
        raise PlaylistError(f"slide {index}: debe ser un objeto")
    ctx = f"slide {index}"
    tipo = raw.get("type")
    if tipo not in {"text", "image", "video", "live", "clock", "color"}:
        raise PlaylistError(f"{ctx}: 'type' debe ser text, image, video, live, clock o color")
    duration = _number(raw, "duration", None, ctx, positive=True, required=True)
    if tipo == "text":
        return _parse_text(raw, ctx, duration)
    if tipo == "image":
        return _parse_image(raw, base, ctx, duration)
    if tipo == "video":
        return _parse_video(raw, base, ctx, duration)
    if tipo == "live":
        return _parse_live(raw, ctx, duration)
    if tipo == "clock":
        return _parse_clock(raw, ctx, duration)
    return _parse_color(raw, ctx, duration)


def _parse_text(raw: dict, ctx: str, duration: float) -> TextSlide:
    _check_keys(
        raw,
        {"type", "duration", "text", "size", "color", "background", "font",
         "align", "valign", "scroll", "speed_px_s"},
        ctx,
    )
    return TextSlide(
        duration=duration,
        text=_string(raw, "text", ctx, required=True),
        size=_integer(raw, "size", 16, ctx, positive=True),
        color=_validate_color(raw.get("color", "#ffffff"), ctx),
        background=_optional_color(raw, "background", ctx),
        font=_string(raw, "font", ctx, default=DEFAULT_FONT),
        align=_choice(raw, "align", "center", {"left", "center", "right"}, ctx),
        valign=_choice(raw, "valign", "middle", {"top", "middle", "bottom"}, ctx),
        scroll=_optional_choice(raw, "scroll", {"left", "right"}, ctx),
        speed_px_s=_number(raw, "speed_px_s", 20.0, ctx, positive=True),
    )


def _parse_image(raw: dict, base: Path, ctx: str, duration: float) -> ImageSlide:
    _check_keys(raw, {"type", "duration", "path", "background", "scroll", "speed_px_s"}, ctx)
    return ImageSlide(
        duration=duration,
        path=base / _string(raw, "path", ctx, required=True),
        background=_optional_color(raw, "background", ctx),
        scroll=_optional_choice(raw, "scroll", {"left", "right"}, ctx),
        speed_px_s=_number(raw, "speed_px_s", 20.0, ctx, positive=True),
    )


def _parse_video(raw: dict, base: Path, ctx: str, duration: float) -> VideoSlide:
    _check_keys(raw, {"type", "duration", "path", "loop", "fps"}, ctx)
    loop = raw.get("loop", True)
    if not isinstance(loop, bool):
        raise PlaylistError(f"{ctx}: 'loop' debe ser booleano")
    return VideoSlide(
        duration=duration,
        path=base / _string(raw, "path", ctx, required=True),
        loop=loop,
        fps=_number(raw, "fps", 30.0, ctx, positive=True),
    )


def _parse_live(raw: dict, ctx: str, duration: float) -> LiveSlide:
    _check_keys(raw, {"type", "duration", "url", "fps", "format", "pixel_format", "size"}, ctx)
    fmt = raw.get("format")
    if fmt not in LIVE_FORMATS:
        raise PlaylistError(
            f"{ctx}: 'format' debe ser uno de {[f for f in LIVE_FORMATS if f]} o ausentarse"
        )
    size = _optional_string(raw, "size", ctx)
    if fmt == "rawvideo" and size is None:
        raise PlaylistError(f"{ctx}: 'format': 'rawvideo' requiere 'size' (ej. \"256x128\")")
    return LiveSlide(
        duration=duration,
        url=_string(raw, "url", ctx, required=True),
        fps=_number(raw, "fps", 30.0, ctx, positive=True),
        format=fmt,
        pixel_format=_optional_string(raw, "pixel_format", ctx),
        size=size,
    )


def _parse_clock(raw: dict, ctx: str, duration: float) -> ClockSlide:
    _check_keys(raw, {"type", "duration", "format", "size", "color", "background", "font"}, ctx)
    fmt = _string(raw, "format", ctx, default="%H:%M:%S")
    _validate_strftime(fmt, ctx)
    return ClockSlide(
        duration=duration,
        fmt=fmt,
        size=_integer(raw, "size", 16, ctx, positive=True),
        color=_validate_color(raw.get("color", "#ffffff"), ctx),
        background=_optional_color(raw, "background", ctx),
        font=_string(raw, "font", ctx, default=DEFAULT_FONT),
    )


def _parse_color(raw: dict, ctx: str, duration: float) -> ColorSlide:
    _check_keys(raw, {"type", "duration", "color"}, ctx)
    return ColorSlide(
        duration=duration,
        color=_validate_color(raw.get("color", "#000000"), ctx),
    )


_STRFTIME_DIRECTIVES = set("aAwdbBmyYHIpMSfzZjUWcxXGuV%")


def _validate_strftime(fmt: str, ctx: str) -> None:
    """Detecta directivas fuera del conjunto documentado de Python.

    En glibc un ``%Q`` desconocido pasa literal en vez de fallar, así que la
    única forma barata de atrapar un typo en la playlist es revisar el texto.
    """
    i = 0
    while i < len(fmt):
        if fmt[i] == "%":
            i += 1
            if i >= len(fmt) or fmt[i] not in _STRFTIME_DIRECTIVES:
                bad = fmt[i] if i < len(fmt) else ""
                raise PlaylistError(f"{ctx}: 'format' inválido cerca de '%{bad}'")
        i += 1


def _string(raw: dict, key: str, ctx: str, *, default: str | None = None, required: bool = False) -> str:
    if key not in raw:
        if required or default is None:
            raise PlaylistError(f"{ctx}: falta '{key}'")
        return default
    value = raw[key]
    if not isinstance(value, str) or not value:
        raise PlaylistError(f"{ctx}: '{key}' debe ser una cadena no vacía")
    return value


def _number(
    raw: dict, key: str, default: float | None, ctx: str,
    *, positive: bool = False, required: bool = False,
) -> float:
    if key not in raw:
        if required or default is None:
            raise PlaylistError(f"{ctx}: falta '{key}'")
        return default
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PlaylistError(f"{ctx}: '{key}' debe ser numérico")
    if positive and value <= 0:
        raise PlaylistError(f"{ctx}: '{key}' debe ser > 0")
    return float(value)


def _integer(
    raw: dict, key: str, default: int | None, ctx: str,
    *, positive: bool = False, required: bool = False,
) -> int:
    if key not in raw:
        if required or default is None:
            raise PlaylistError(f"{ctx}: falta '{key}'")
        return default
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise PlaylistError(f"{ctx}: '{key}' debe ser entero")
    if positive and value <= 0:
        raise PlaylistError(f"{ctx}: '{key}' debe ser > 0")
    return value


def _choice(raw: dict, key: str, default: str, options: set[str], ctx: str) -> str:
    value = raw.get(key, default)
    if value not in options:
        raise PlaylistError(f"{ctx}: '{key}' debe ser uno de {sorted(options)}")
    return value


def _optional_choice(raw: dict, key: str, options: set[str], ctx: str) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if value not in options:
        raise PlaylistError(f"{ctx}: '{key}' debe ser uno de {sorted(options)}")
    return value


def _optional_string(raw: dict, key: str, ctx: str) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise PlaylistError(f"{ctx}: '{key}' debe ser una cadena no vacía")
    return value


def _validate_color(value: Any, ctx: str) -> str:
    if not isinstance(value, str):
        raise PlaylistError(f"{ctx}: el color debe ser una cadena #rrggbb")
    try:
        hex_to_rgb(value)
    except ValueError as exc:
        raise PlaylistError(f"{ctx}: {exc}") from exc
    return value


def _optional_color(raw: dict, key: str, ctx: str) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    return _validate_color(value, ctx)
