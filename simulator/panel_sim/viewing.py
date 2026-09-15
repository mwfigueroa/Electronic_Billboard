"""Emulación de la distancia de observación (docs/01, docs/14).

El panel del proyecto mide 256 px × 5 mm de paso = 1280 mm de ancho. Para que
un monitor reproduzca el **ángulo visual** de mirar el cartel desde D metros,
la ventana debe medir ``ancho_físico_del_panel × distancia_ojo / D``
milímetros. De ahí salen el tamaño de ventana para una distancia objetivo y la
distancia equivalente de una ventana cualquiera.

La calibración del monitor es del usuario: diagonal, ancho en píxeles y su
distancia normal a la pantalla. ``ViewingSetup`` trae valores razonables por
defecto (24", 1920 px, 60 cm) que se deben ajustar para que la emulación sea
fiel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

MM_PER_INCH = 25.4
ASPECT = (16, 9)


def monitor_width_mm(diagonal_inch: float, aspect: tuple[int, int] = ASPECT) -> float:
    """Ancho físico del monitor a partir de la diagonal y el aspecto."""
    w, h = aspect
    return diagonal_inch * MM_PER_INCH * w / math.hypot(w, h)


def mm_per_pixel(
    diagonal_inch: float,
    monitor_width_px: int,
    aspect: tuple[int, int] = ASPECT,
) -> float:
    """Milímetros de pantalla por píxel lógico del monitor."""
    return monitor_width_mm(diagonal_inch, aspect) / monitor_width_px


def window_px_for_distance(
    panel_w_px: int,
    panel_h_px: int,
    pitch_mm: float,
    distance_m: float,
    monitor_mm_per_px: float,
    eye_m: float,
) -> tuple[int, int]:
    """Ventana (px) que emula exactamente ``distance_m`` en el monitor dado."""
    scale = pitch_mm * eye_m / (distance_m * monitor_mm_per_px)
    return max(2, round(panel_w_px * scale)), max(2, round(panel_h_px * scale))


def equivalent_distance_m(
    panel_w_px: int,
    pitch_mm: float,
    scale: float,
    monitor_mm_per_px: float,
    eye_m: float,
) -> float:
    """Distancia real que reproduce una ventana de ``scale`` px por píxel."""
    panel_mm = panel_w_px * pitch_mm
    screen_mm = panel_w_px * scale * monitor_mm_per_px
    return panel_mm * eye_m / screen_mm


@dataclass(frozen=True)
class ViewingSetup:
    pitch_mm: float = 5.0
    monitor_inch: float = 24.0
    monitor_px: int = 1920
    aspect: tuple[int, int] = ASPECT
    eye_cm: float = 60.0

    @property
    def eye_m(self) -> float:
        return self.eye_cm / 100.0

    @property
    def mm_per_px(self) -> float:
        return mm_per_pixel(self.monitor_inch, self.monitor_px, self.aspect)

    @property
    def aspect_label(self) -> str:
        return f"{self.aspect[0]}:{self.aspect[1]}"

    def window_for(self, panel_w_px: int, panel_h_px: int, distance_m: float) -> tuple[int, int]:
        return window_px_for_distance(
            panel_w_px, panel_h_px, self.pitch_mm, distance_m, self.mm_per_px, self.eye_m
        )

    def equivalent(self, panel_w_px: int, scale: float) -> float:
        return equivalent_distance_m(
            panel_w_px, self.pitch_mm, scale, self.mm_per_px, self.eye_m
        )

    def min_distance_m(self, panel_w_px: int, panel_h_px: int, max_scale: float) -> float:
        """Distancia mínima que entra en pantalla con una escala dada."""
        return self.pitch_mm * self.eye_m / (max_scale * self.mm_per_px)
