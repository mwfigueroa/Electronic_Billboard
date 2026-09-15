"""Simulador de panel — pipeline de contenido del cartel.

Referencia de software de docs/14_software_contenido.md:
playlist → canvas 256×128 RGB888 → gamma y cuantización → bitplanes.

La conversión RGB → bitplanes es la implementación de referencia contra la
cual se valida ``rgb_to_bitplane`` del HDL.
"""

__version__ = "0.1.0"

from .bitplanes import bitplanes_to_rgb, canonical_test_frame, rgb_to_bitplanes
from .playlist import (
    ClockSlide,
    ColorSlide,
    Display,
    ImageSlide,
    Playlist,
    PlaylistError,
    Slide,
    TextSlide,
    VideoSlide,
    load,
)
from .quantize import levels_count, quantize, to_display
from .timeline import Timeline
from .timing import CLOCKS_PER_BITPLANE, frame_clocks, refresh_hz

__all__ = [
    "CLOCKS_PER_BITPLANE",
    "ClockSlide",
    "ColorSlide",
    "Display",
    "ImageSlide",
    "Playlist",
    "PlaylistError",
    "Slide",
    "TextSlide",
    "Timeline",
    "VideoSlide",
    "bitplanes_to_rgb",
    "canonical_test_frame",
    "frame_clocks",
    "levels_count",
    "load",
    "quantize",
    "refresh_hz",
    "rgb_to_bitplanes",
    "to_display",
]
