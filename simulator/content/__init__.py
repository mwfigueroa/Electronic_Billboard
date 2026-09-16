"""App de contenido — el lado PC del contrato de wire v1 (docs/14).

Compone la playlist declarativa a frames RGB888 de 256×128 y termina ahí: no
sabe nada de LED, gamma ni profundidad de color. Eso vive en ``panel_sim``
(el lado panel), y la frontera entre ambos paquetes es el contrato.

    playlist → canvas → timeline → frames RGB888
"""

from .canvas import (
    contain,
    hex_to_rgb,
    new_canvas,
    paste_aligned,
    resolve_font,
    scale_with_grid,
    text_image,
)
from .playlist import (
    ClockSlide,
    ColorSlide,
    DIAS,
    Display,
    ImageSlide,
    LiveSlide,
    Playlist,
    PlaylistError,
    Schedule,
    Slide,
    TextSlide,
    VideoSlide,
    is_active,
    load,
    parse,
)
from .timeline import Timeline
from .video import VideoError, VideoSource, ffmpeg_exe

__all__ = [
    "ClockSlide",
    "ColorSlide",
    "DIAS",
    "Display",
    "ImageSlide",
    "LiveSlide",
    "Playlist",
    "PlaylistError",
    "Schedule",
    "Slide",
    "TextSlide",
    "Timeline",
    "VideoError",
    "VideoSlide",
    "VideoSource",
    "contain",
    "ffmpeg_exe",
    "hex_to_rgb",
    "is_active",
    "load",
    "new_canvas",
    "parse",
    "paste_aligned",
    "resolve_font",
    "scale_with_grid",
    "text_image",
]
