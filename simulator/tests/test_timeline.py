import numpy as np
import pytest
from PIL import Image

from panel_sim.playlist import (
    ClockSlide,
    ColorSlide,
    Display,
    ImageSlide,
    Playlist,
    TextSlide,
)
from panel_sim.timeline import Timeline


def _playlist(*slides, **display_kwargs):
    return Playlist(
        display=Display(**display_kwargs),
        slides=tuple(slides),
        source=None,  # type: ignore[arg-type]
    )


def test_locate_wraps():
    pl = _playlist(
        ColorSlide(duration=2.0, color="#000000"),
        ColorSlide(duration=3.0, color="#ffffff"),
    )
    tl = Timeline(pl)
    assert tl.duration == 5.0
    assert tl.locate(0.0) == (0, 0.0)
    assert tl.locate(1.5) == (0, 1.5)
    assert tl.locate(2.0) == (1, 0.0)
    index, local = tl.locate(4.9)
    assert index == 1
    assert local == pytest.approx(2.9)
    assert tl.locate(6.0) == (0, 1.0)


def test_locate_ignores_negative_and_overflow():
    pl = _playlist(ColorSlide(duration=4.0, color="#000000"))
    tl = Timeline(pl)
    assert tl.locate(-1.0) == (0, 3.0)
    assert tl.locate(9.0) == (0, 1.0)


def test_color_frame():
    pl = _playlist(ColorSlide(duration=1.0, color="#102030"), width=8, height=4)
    frame = Timeline(pl).frame(0.0)
    assert frame.shape == (4, 8, 3)
    assert frame.dtype == np.uint8
    assert np.all(frame == (0x10, 0x20, 0x30))


def test_clock_frame_has_content():
    from datetime import datetime

    pl = _playlist(ClockSlide(duration=2.0, size=16, color="#ffffff"), width=128, height=64)
    frame = Timeline(pl).frame_at(0, 0.0, now=datetime(2026, 9, 15, 12, 34, 56))
    assert frame.max() == 255
    assert (frame > 0).any()


def test_scroll_enters_canvas():
    slide = TextSlide(
        duration=10.0, text="HOLA", size=16, color="#ffffff",
        scroll="left", speed_px_s=64.0,
    )
    tl = Timeline(_playlist(slide, width=128, height=32))
    assert tl.frame_at(0, 0.0).sum() == 0
    assert tl.frame_at(0, 2.0).sum() > 0


def test_scroll_directions_differ():
    common = dict(duration=10.0, text="HOLA", size=16, color="#ffffff", speed_px_s=64.0)
    left = Timeline(_playlist(TextSlide(**common, scroll="left"), width=128, height=32))
    right = Timeline(_playlist(TextSlide(**common, scroll="right"), width=128, height=32))
    xs_left = np.nonzero(left.frame_at(0, 1.0)[:, :, 0])[1]
    xs_right = np.nonzero(right.frame_at(0, 1.0)[:, :, 0])[1]
    assert len(xs_left) > 0 and len(xs_right) > 0
    assert xs_left.mean() > 64
    assert xs_right.mean() < 64


def test_scrolled_image_keeps_width(tmp_path):
    path = tmp_path / "banner.png"
    Image.new("RGB", (800, 60), (255, 255, 255)).save(path)
    slide = ImageSlide(duration=20.0, path=path, scroll="left", speed_px_s=64.0)
    tl = Timeline(_playlist(slide, width=256, height=128))
    assert tl.frame_at(0, 0.0).sum() == 0
    frame = tl.frame_at(0, 7.9)
    assert (frame[:, :, 0] == 255).sum() > 255 * 30


def test_static_text_centered():
    slide = TextSlide(duration=10.0, text="X", size=16, color="#ffffff")
    tl = Timeline(_playlist(slide, width=64, height=32))
    frame = tl.frame_at(0, 0.0)
    ys, xs = np.nonzero(frame[:, :, 0])
    assert len(xs) > 0
    assert abs(xs.mean() - 32) < 12
    assert abs(ys.mean() - 16) < 12


def test_timeout_guard_no_slides():
    with pytest.raises(ValueError):
        Timeline(Playlist(display=Display(), slides=(), source=None))  # type: ignore[arg-type]
