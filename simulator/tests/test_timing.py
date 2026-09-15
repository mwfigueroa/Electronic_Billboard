import pytest

from panel_sim.timing import CLOCKS_PER_BITPLANE, frame_clocks, refresh_hz


@pytest.mark.parametrize(
    "depth,hz",
    [(4, 400.6), (5, 193.9), (6, 95.4)],
)
def test_table_12_5_mhz(depth, hz):
    assert refresh_hz(12.5e6, depth) == pytest.approx(hz, rel=0.01)


@pytest.mark.parametrize(
    "depth,hz",
    [(4, 801.3), (5, 387.7), (6, 190.8)],
)
def test_table_25_mhz(depth, hz):
    assert refresh_hz(25e6, depth) == pytest.approx(hz, rel=0.01)


def test_frame_clocks():
    assert frame_clocks(5) == CLOCKS_PER_BITPLANE * 31
