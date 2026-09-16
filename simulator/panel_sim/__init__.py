"""Simulador de panel — el lado panel del contrato de wire v1 (docs/14).

Toma frames RGB888 de 256×128 y hace lo que hará el hardware: gamma,
cuantización a N bits, bitplanes, temporización BCM y máscara de LED. Incluye
el visor del panel virtual, la emulación de distancia y los vectores dorados
para el HDL.

La composición de contenido vive en ``content`` (lado app); acá no se compone
nada, solo se consume lo que el contrato define.
"""

__version__ = "0.1.0"

from .bitplanes import bitplanes_to_rgb, canonical_test_frame, rgb_to_bitplanes
from .quantize import levels_count, quantize, to_display
from .timing import CLOCKS_PER_BITPLANE, frame_clocks, refresh_hz
from .viewing import ViewingSetup

__all__ = [
    "CLOCKS_PER_BITPLANE",
    "ViewingSetup",
    "bitplanes_to_rgb",
    "canonical_test_frame",
    "frame_clocks",
    "levels_count",
    "quantize",
    "refresh_hz",
    "rgb_to_bitplanes",
    "to_display",
]
