import numpy as np
import pytest

from panel_sim.bitplanes import (
    bitplanes_to_rgb,
    canonical_test_frame,
    rgb_to_bitplanes,
)


def test_roundtrip_all_depths():
    rng = np.random.default_rng(7)
    for depth in (4, 5, 6):
        levels = rng.integers(0, 1 << depth, size=(8, 16, 3), dtype=np.uint8)
        planes = rgb_to_bitplanes(levels, depth)
        assert planes.shape == (depth, 3, 8, 16)
        assert set(np.unique(planes)) <= {0, 1}
        np.testing.assert_array_equal(bitplanes_to_rgb(planes), levels)


def test_lsb_convention():
    levels = np.zeros((1, 1, 3), dtype=np.uint8)
    levels[0, 0, 0] = 1
    planes = rgb_to_bitplanes(levels, 4)
    assert planes[0, 0, 0, 0] == 1
    assert planes[1, 0, 0, 0] == 0
    assert planes[0, 1, 0, 0] == 0


def test_rejects_out_of_range():
    levels = np.zeros((1, 1, 3), dtype=np.uint8)
    levels[0, 0, 0] = 32
    with pytest.raises(ValueError, match="fuera de rango"):
        rgb_to_bitplanes(levels, 5)


def test_rejects_negative():
    levels = np.array([[[-1, 0, 0]]], dtype=np.int16)
    with pytest.raises(ValueError, match="fuera de rango"):
        rgb_to_bitplanes(levels, 5)


def test_canonical_frame():
    frame = canonical_test_frame(16, 8)
    assert frame.shape == (8, 16, 3)
    assert frame.dtype == np.uint8
    assert frame[0, 0, 0] == 0
    assert frame[0, 15, 0] == 255
    assert frame[7, 0, 1] == 255
    assert frame[0, 0, 2] == 0
    assert frame[0, 1, 2] == 255
