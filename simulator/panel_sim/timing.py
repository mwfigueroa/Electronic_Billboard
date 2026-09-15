"""Tasa de refresco del modelo BCM (docs/11_arquitectura_colorlight_5a75b.md).

Un frame BCM con ``depth`` bits por color dura ``clocks_per_bitplane ×
(2^depth − 1)`` clocks de panel: los ocho puertos van en lockstep y comparten
ese tiempo.

``CLOCKS_PER_BITPLANE = 2048`` sale de la fórmula general de docs/10 —
``(ancho × alto) ÷ (2 grupos × N buses)`` = 32768 ÷ 16 — o, por cadena,
``2 módulos × 64×32 px ÷ 2 grupos R1/R2``. La división es por los dos grupos
que desplazan en paralelo, no por filas: docs/10 registra que ese factor de 2
ya se erró una vez. Verificado contra la tabla de docs/11: 12,5 MHz, 5 bits →
~197 Hz.
"""

CLOCKS_PER_BITPLANE = 2048


def frame_clocks(depth: int, clocks_per_bitplane: int = CLOCKS_PER_BITPLANE) -> int:
    return clocks_per_bitplane * ((1 << depth) - 1)


def refresh_hz(
    pixel_clock_hz: float,
    depth: int,
    clocks_per_bitplane: int = CLOCKS_PER_BITPLANE,
) -> float:
    return pixel_clock_hz / frame_clocks(depth, clocks_per_bitplane)
