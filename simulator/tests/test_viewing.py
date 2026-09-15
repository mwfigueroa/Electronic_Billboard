import pytest

from panel_sim.viewing import (
    ViewingSetup,
    equivalent_distance_m,
    mm_per_pixel,
    monitor_width_mm,
    window_px_for_distance,
)

SETUP = ViewingSetup()


def test_monitor_width_mm_24in():
    assert monitor_width_mm(24) == pytest.approx(531.3, rel=0.01)


def test_mm_per_pixel_24in_1080p():
    assert mm_per_pixel(24, 1920) == pytest.approx(0.2767, rel=0.01)


def test_window_for_5m_24in_60cm():
    assert SETUP.window_for(256, 128, 5.0) == (555, 278)


def test_roundtrip_distance():
    w, _ = SETUP.window_for(256, 128, 5.0)
    assert SETUP.equivalent(256, w / 256) == pytest.approx(5.0, rel=0.01)


def test_closer_distance_gives_bigger_window():
    near = SETUP.window_for(256, 128, 3.0)
    far = SETUP.window_for(256, 128, 10.0)
    assert near[0] > far[0] > 0
    assert near[1] > far[1] > 0


def test_equivalent_scale_2_24in_60cm():
    mmpx = mm_per_pixel(24, 1920)
    assert equivalent_distance_m(256, 5.0, 2.0, mmpx, 0.60) == pytest.approx(5.42, rel=0.02)


def test_min_distance_fits_desktop():
    min_d = SETUP.min_distance_m(256, 128, max_scale=4.0)
    w, h = window_px_for_distance(256, 128, 5.0, min_d, SETUP.mm_per_px, SETUP.eye_m)
    assert w <= 256 * 4 and h <= 128 * 4


def test_pitch_scales_linearly():
    """Con pitch 10 mm (P10) la ventana emulada duplica su tamaño a igual distancia."""
    p5 = ViewingSetup(pitch_mm=5.0).window_for(256, 128, 5.0)
    p10 = ViewingSetup(pitch_mm=10.0).window_for(256, 128, 5.0)
    assert p10[0] == pytest.approx(p5[0] * 2, rel=0.01)
