import pytest

from panel_sim.timing import CLOCKS_PER_BITPLANE, frame_clocks, refresh_hz


@pytest.mark.parametrize(
    "depth,hz",
    [(4, 407.0), (5, 197.0), (6, 97.0)],
)
def test_table_12_5_mhz(depth, hz):
    assert refresh_hz(12.5e6, depth) == pytest.approx(hz, rel=0.01)


@pytest.mark.parametrize(
    "depth,hz",
    [(4, 814.0), (5, 394.0), (6, 194.0)],
)
def test_table_25_mhz(depth, hz):
    assert refresh_hz(25e6, depth) == pytest.approx(hz, rel=0.01)


def test_frame_clocks():
    assert frame_clocks(5) == CLOCKS_PER_BITPLANE * 31
