import os

import numpy as np
from panel_sim.viewer import (
    _gap_geometry,
    layout_panel,
    pixel_dot_array,
    pixel_mask_array,
    render_surface,
)


def test_pixel_mask_led_and_gap():
    mask = pixel_mask_array(2, 1, cell=4, gap=1)
    assert mask.shape == (4, 8)
    assert mask.sum() == 2 * 3 * 3
    assert not mask[0, 3]
    assert not mask[3, 0]


def test_pixel_dot_round_is_soft():
    arr = pixel_dot_array(1, 1, 10, 6)
    assert arr.shape == (10, 10)
    assert arr.min() >= 0.0
    assert arr.max() <= 1.0
    assert arr[4, 4] == 1.0
    assert arr[0, 0] == 0.0
    assert arr.sum() < 16  # el círculo pesa menos que el cuadrado 4×4


def test_pixel_dot_square_fallback():
    arr = pixel_dot_array(1, 1, 10, 6, round_dot=False)
    assert arr.sum() == 16


def test_pixel_dot_disabled():
    assert pixel_dot_array(2, 1, 4, 0).all()
    assert pixel_dot_array(2, 1, 1, 1).all()


def test_pixel_mask_gap_is_black_between_cells():
    mask = pixel_mask_array(3, 2, cell=3, gap=1)
    assert mask.shape == (6, 9)  # 2 celdas de alto, 3 de ancho, celda 3×3
    assert mask.sum() == 3 * 2 * 2 * 2


def test_pixel_mask_disabled():
    assert pixel_mask_array(2, 1, 4, 0).all()
    assert pixel_mask_array(2, 1, 1, 1).all()
    assert pixel_mask_array(2, 1, 3, 3).all()


def test_gap_geometry_below_five_px_no_mask():
    """Con celda < 5 px la máscara no puede ser fiel: no se dibuja."""
    assert _gap_geometry(768, 256, 0.3) == (3, 0)
    assert _gap_geometry(1024, 256, 0.3) == (4, 0)
    assert _gap_geometry(416, 256, 0.3) == (1, 0)
    assert _gap_geometry(768, 256, 0.0) == (3, 0)


def test_gap_geometry_more_separation():
    assert _gap_geometry(1280, 256, 0.5) == (5, 2)
    assert _gap_geometry(1536, 256, 0.5) == (6, 3)


def test_gap_geometry_matches_reference_photo():
    """Foto del P5: LED ≈ 1/3 del paso → gap_frac 0.65."""
    assert _gap_geometry(1536, 256, 0.65) == (6, 4)  # LED 2/6 = 33 %
    assert _gap_geometry(2048, 256, 0.65) == (8, 5)  # LED 3/8 = 37 %


def test_gap_geometry_led_never_below_two():
    assert _gap_geometry(1280, 256, 0.9) == (5, 3)  # LED 1 se vería apagado


def test_layout_panel_snaps_to_whole_cells_with_mask():
    """Con máscara, el panel se ajusta a celdas enteras para no reescalar."""
    panel, x, y = layout_panel((1300, 700), 256, 128, 0.65)
    assert panel == (1280, 640)
    assert x == 10
    assert y == 18


def test_layout_panel_exact_without_mask():
    panel, x, y = layout_panel((1024, 536), 256, 128, 0.65)
    assert panel == (1024, 512)
    assert (x, y) == (0, 0)


def test_render_surface_applies_mask():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame

    pygame.init()
    pygame.display.set_mode((64, 64))
    frame = np.full((4, 8, 3), 255, dtype=np.uint8)
    plain = render_surface(frame, (16, 8), None, 0)
    assert plain.get_at((0, 0))[:3] == (255, 255, 255)
    black = pygame.Surface((16, 8))
    black.fill((0, 0, 0))
    masked = render_surface(frame, (16, 8), black, 2)
    assert masked.get_at((0, 0))[:3] == (0, 0, 0)
    pygame.quit()
