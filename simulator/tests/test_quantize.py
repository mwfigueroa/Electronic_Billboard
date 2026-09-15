import numpy as np
import pytest

from panel_sim.quantize import levels_count, quantize, to_display


def test_levels_count():
    assert levels_count(4) == 16
    assert levels_count(5) == 32
    assert levels_count(8) == 256


@pytest.mark.parametrize("depth", [0, 9, -1])
def test_levels_count_invalid(depth):
    with pytest.raises(ValueError):
        levels_count(depth)


@pytest.mark.parametrize("depth", [4, 5, 6])
def test_extremes(depth):
    max_level = levels_count(depth) - 1
    frame = np.array([[[0, 0, 0], [255, 255, 255]]], dtype=np.uint8)
    levels = quantize(frame, depth, 2.2)
    assert tuple(levels[0, 0]) == (0, 0, 0)
    assert tuple(levels[0, 1]) == (max_level, max_level, max_level)


def test_monotonic_ramp():
    ramp = np.arange(256, dtype=np.uint8).reshape(256, 1, 1).repeat(3, axis=2)
    levels = quantize(ramp, 5, 2.2)[:, 0, 0].astype(int)
    assert np.all(np.diff(levels) >= 0)
    assert levels[0] == 0
    assert levels[-1] == 31


def test_gamma_linear_is_direct_scaling():
    frame = np.array([[[128, 64, 255]]], dtype=np.uint8)
    levels = quantize(frame, 8, 1.0)
    assert tuple(levels[0, 0]) == (128, 64, 255)


def test_gamma_darkens_gamma_22():
    mid = np.array([[[128, 128, 128]]], dtype=np.uint8)
    assert quantize(mid, 8, 2.2)[0, 0, 0] < 128


def test_to_display_monitor_encoding():
    levels = np.array([[[0, 15, 31]]], dtype=np.uint8)
    out = to_display(levels, 5)
    assert tuple(out[0, 0]) == (0, 183, 255)


def test_preview_midgray_gamma_corrected():
    """Con gamma 2.2, el gris medio del panel se ve ~130 en un monitor sRGB."""
    mid = np.array([[[128, 128, 128]]], dtype=np.uint8)
    preview = to_display(quantize(mid, 5, 2.2), 5)
    assert abs(int(preview[0, 0, 0]) - 130) <= 2


def test_preview_midgray_gamma_1_is_washed_out():
    """Sin corrección (gamma 1) el panel crudo muestra el gris medio ~189."""
    mid = np.array([[[128, 128, 128]]], dtype=np.uint8)
    preview = to_display(quantize(mid, 5, 1.0), 5)
    assert abs(int(preview[0, 0, 0]) - 189) <= 2


def test_roundtrip_preserves_midtones():
    """quantize(gamma 2.2) → to_display ≈ entrada: el panel se ve como el original."""
    for v in (96, 128, 160, 192, 255):
        frame = np.full((1, 1, 3), v, np.uint8)
        out = int(to_display(quantize(frame, 5, 2.2), 5)[0, 0, 0])
        assert abs(out - v) <= 6, f"v={v}: preview={out}"


def test_to_display_monotonic():
    levels = np.arange(32, dtype=np.uint8).reshape(32, 1, 1).repeat(3, axis=2)
    out = to_display(levels, 5)[:, 0, 0].astype(int)
    assert np.all(np.diff(out) >= 0)
    assert out[0] == 0
    assert out[-1] == 255
