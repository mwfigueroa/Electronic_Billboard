import json
from pathlib import Path

import pytest

from panel_sim.playlist import (
    Display,
    ImageSlide,
    PlaylistError,
    TextSlide,
    VideoSlide,
    load,
)

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
EXAMPLE = EXAMPLES / "playlist.json"


def _write(tmp_path, slides, display=None, **top):
    doc = {"version": 1, "display": display or {}, "slides": slides}
    doc.update(top)
    path = tmp_path / "playlist.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def test_load_example():
    playlist = load(EXAMPLE)
    assert playlist.display.width == 256
    assert playlist.display.height == 128
    assert playlist.display.depth == 5
    assert len(playlist.slides) >= 4
    assert playlist.duration == pytest.approx(sum(s.duration for s in playlist.slides))
    assert any(isinstance(s, TextSlide) for s in playlist.slides)


def test_example_image_paths_resolve_relative():
    playlist = load(EXAMPLE)
    images = [s for s in playlist.slides if isinstance(s, ImageSlide)]
    assert images, "el ejemplo no tiene slides de imagen"
    for image in images:
        assert image.path.parent == EXAMPLES
        assert image.path.exists(), f"falta {image.path.name}"
    assert EXAMPLES / "logo.png" in {i.path for i in images}


def test_defaults(tmp_path):
    playlist = load(_write(tmp_path, [{"type": "color", "duration": 1}]))
    assert playlist.display == Display()
    assert playlist.version == 1


def test_video_slide(tmp_path):
    playlist = load(_write(tmp_path, [{"type": "video", "duration": 5, "path": "clip.mp4"}]))
    slide = playlist.slides[0]
    assert isinstance(slide, VideoSlide)
    assert slide.path == tmp_path / "clip.mp4"
    assert slide.loop is True
    assert slide.fps == 30.0


def test_video_bad_loop(tmp_path):
    path = _write(
        tmp_path,
        [{"type": "video", "duration": 5, "path": "clip.mp4", "loop": "sí"}],
    )
    with pytest.raises(PlaylistError, match="loop"):
        load(path)


def test_load_example_video():
    playlist = load(EXAMPLES / "playlist_video.json")
    slide = playlist.slides[0]
    assert isinstance(slide, VideoSlide)
    assert slide.path.resolve() == (EXAMPLES.parent / "media" / "sintel_10s.mp4").resolve()
    assert slide.loop is True
    assert playlist.slides[1].type == "text"


def test_unknown_key(tmp_path):
    path = _write(tmp_path, [{"type": "color", "duration": 1, "duraton": 2}])
    with pytest.raises(PlaylistError, match="desconocidas"):
        load(path)


def test_missing_duration(tmp_path):
    path = _write(tmp_path, [{"type": "color", "color": "#ffffff"}])
    with pytest.raises(PlaylistError, match="duration"):
        load(path)


def test_unknown_type(tmp_path):
    path = _write(tmp_path, [{"type": "audio", "duration": 1}])
    with pytest.raises(PlaylistError, match="type"):
        load(path)


def test_bad_scroll(tmp_path):
    path = _write(tmp_path, [{"type": "text", "duration": 1, "text": "X", "scroll": "up"}])
    with pytest.raises(PlaylistError, match="scroll"):
        load(path)


def test_bad_color(tmp_path):
    path = _write(tmp_path, [{"type": "color", "duration": 1, "color": "azul"}])
    with pytest.raises(PlaylistError, match="color"):
        load(path)


def test_empty_slides(tmp_path):
    path = _write(tmp_path, [])
    with pytest.raises(PlaylistError, match="slides"):
        load(path)


def test_bad_depth(tmp_path):
    path = _write(tmp_path, [{"type": "color", "duration": 1}], display={"depth": 12})
    with pytest.raises(PlaylistError, match="depth"):
        load(path)


def test_bad_clock_format(tmp_path):
    path = _write(tmp_path, [{"type": "clock", "duration": 1, "format": "%Q"}])
    with pytest.raises(PlaylistError, match="format"):
        load(path)


def test_missing_file(tmp_path):
    with pytest.raises(PlaylistError, match="no existe"):
        load(tmp_path / "nada.json")
