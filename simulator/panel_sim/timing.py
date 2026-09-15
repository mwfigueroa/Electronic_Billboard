"""Tasa de refresco del modelo BCM (docs/11_arquitectura_colorlight_5a75b.md).

Un frame BCM con ``depth`` bits por color dura ``clocks_per_bitplane ×
(2^depth − 1)`` clocks de panel: los ocho puertos van en lockstep y comparten
ese tiempo.

Los 2048 clocks de datos por bitplane salen de la fórmula general de docs/10 —
``(ancho × alto) ÷ (2 grupos × N buses)`` = 32768 ÷ 16 — o, por cadena,
``2 módulos × 64×32 px ÷ 2 grupos R1/R2``. La división es por los dos grupos
que desplazan en paralelo, no por filas: docs/10 registra que ese factor de 2
ya se erró una vez.

El secuenciador implementado (``driver-5a75b/bcm_sequencer``) agrega 4 clocks
de blanking por paso de dirección —8 pasos— para latchear y asentar la fila
con ``OE`` en bajo, así que ``CLOCKS_PER_BITPLANE = 2080``. Verificado contra
la simulación: 12,5 MHz y 5 bits dan 193,9 Hz.
"""

CLOCKS_PER_BITPLANE = 2080


def frame_clocks(depth: int, clocks_per_bitplane: int = CLOCKS_PER_BITPLANE) -> int:
    return clocks_per_bitplane * ((1 << depth) - 1)


def refresh_hz(
    pixel_clock_hz: float,
    depth: int,
    clocks_per_bitplane: int = CLOCKS_PER_BITPLANE,
) -> float:
    return pixel_clock_hz / frame_clocks(depth, clocks_per_bitplane)
