"""Gamma y cuantización a N bits por color.

Hay dos gammas distintas y no hay que mezclarlas:

- La de **autoría/panel** (``quantize``): lleva el valor codificado (sRGB) al
  ciclo de trabajo del panel, ``duty = (v/255)**gamma``. El panel BCM es
  lineal en luz, así que ``gamma=2.2`` reproduce la respuesta sRGB; ``gamma=1``
  es el panel crudo, que muestra los medios tonos demasiado brillantes.
- La del **monitor** (``to_display``, fija en ``DISPLAY_GAMMA``): para que el
  PNG y el visor muestren la luz que emitiría el panel, el duty se re-codifica
  a sRGB con ``duty ** (1/DISPLAY_GAMMA)``. Sin este paso todo preview sale
  mucho más oscuro que el panel real y el costo de la cuantización parece
  mayor de lo que es. No depende de la gamma de la playlist.
"""

from __future__ import annotations

import numpy as np

DISPLAY_GAMMA = 2.2


def levels_count(depth: int) -> int:
    if not 1 <= depth <= 8:
        raise ValueError(f"profundidad fuera de rango: {depth} (1..8)")
    return 1 << depth


def quantize(frame: np.ndarray, depth: int, gamma: float = 2.2) -> np.ndarray:
    """RGB888 (h,w,3) uint8 → niveles 0..2^depth-1, uint8."""
    max_level = levels_count(depth) - 1
    v = frame.astype(np.float64) / 255.0
    if gamma != 1.0:
        v = np.power(v, gamma)
    return np.rint(v * max_level).astype(np.uint8)


def to_display(levels: np.ndarray, depth: int) -> np.ndarray:
    """Niveles → RGB888 para monitor sRGB: simula la luz del panel.

    El monitor decodifica el PNG con su respuesta sRGB (``v**2.2``); el panel
    emite ``duty`` lineal. Para que ambos coincidan, el PNG se codifica con
    ``duty ** (1/2.2)``.
    """
    max_level = levels_count(depth) - 1
    duty = levels.astype(np.float64) / max_level
    return np.rint(255.0 * np.power(duty, 1.0 / DISPLAY_GAMMA)).astype(np.uint8)
