"""Conversión RGB → bitplanes: referencia de oro del HDL.

Layout canónico ``[bit, canal, y, x]``, bit 0 = LSB, ``x`` creciente hacia la
derecha del canvas. Es **pre-mapeo**: el scan 1/8 y el orden real de la cadena
son específicos del panel y se resuelven en ``scan_mapper``
(docs/11_arquitectura_colorlight_5a75b.md). El HDL se valida contra estos
mismos valores; ver ``vectors.py`` para los archivos de testbench.
"""

from __future__ import annotations

import numpy as np

from .quantize import levels_count


def rgb_to_bitplanes(levels: np.ndarray, depth: int) -> np.ndarray:
    """(h,w,3) niveles → (depth,3,h,w) bits 0/1.

    Valida el rango: un nivel ≥ 2^depth se truncaría en silencio, y acá esta
    función es la referencia de oro del HDL — conviene que grite.
    """
    max_level = levels_count(depth) - 1
    levels = np.asarray(levels)
    if levels.size and (int(levels.max()) > max_level or int(levels.min()) < 0):
        raise ValueError(
            f"niveles fuera de rango para {depth} bits (0..{max_level}): "
            f"[{int(levels.min())}, {int(levels.max())}]"
        )
    channels = levels.transpose(2, 0, 1)
    bits = (channels[None, ...] >> np.arange(depth)[:, None, None, None]) & 1
    return bits.astype(np.uint8)


def bitplanes_to_rgb(bitplanes: np.ndarray) -> np.ndarray:
    """(depth,3,h,w) bits → (h,w,3) niveles."""
    value = np.zeros(bitplanes.shape[1:], dtype=np.uint16)
    for bit in range(bitplanes.shape[0]):
        value |= bitplanes[bit].astype(np.uint16) << bit
    return value.transpose(1, 2, 0).astype(np.uint8)


def canonical_test_frame(width: int = 16, height: int = 8) -> np.ndarray:
    """Patrón determinista: R horizontal, G vertical, B = damero en (x+y) impar."""
    x = np.arange(width, dtype=np.float64)
    y = np.arange(height, dtype=np.float64)
    r = np.rint(x * 255.0 / max(width - 1, 1))
    g = np.rint(y * 255.0 / max(height - 1, 1))
    b = ((x[None, :] + y[:, None]) % 2) * 255.0
    frame = np.stack(
        [
            np.broadcast_to(r, (height, width)),
            np.broadcast_to(g[:, None], (height, width)),
            b,
        ],
        axis=-1,
    )
    return frame.astype(np.uint8)
