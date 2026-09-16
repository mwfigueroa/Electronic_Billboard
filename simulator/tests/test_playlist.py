import json
from datetime import datetime, time as dt_time
from pathlib import Path

import pytest

from content.playlist import (
    DIAS,
    Display,
    ImageSlide,
    LiveSlide,
    PlaylistError,
    Schedule,
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


def test_live_slide_udp(tmp_path):
    path = _write(
        tmp_path,
        [{
            "type": "live", "duration": 60,
            "url": "udp://127.0.0.1:5000",
            "format": "rawvideo", "size": "256x128",
        }],
    )
    slide = load(path).slides[0]
    assert isinstance(slide, LiveSlide)
    assert slide.url == "udp://127.0.0.1:5000"
    assert slide.input_args == (
        "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", "256x128",
    )


def test_live_slide_http_autodetecta(tmp_path):
    path = _write(
        tmp_path,
        [{"type": "live", "duration": 10, "url": "http://127.0.0.1:8080/stream.mjpg"}],
    )
    slide = load(path).slides[0]
    assert isinstance(slide, LiveSlide)
    assert slide.input_args == ()


def test_live_rawvideo_requires_size(tmp_path):
    path = _write(
        tmp_path,
        [{"type": "live", "duration": 10, "url": "udp://127.0.0.1:5000", "format": "rawvideo"}],
    )
    with pytest.raises(PlaylistError, match="size"):
        load(path)


def test_live_bad_format(tmp_path):
    path = _write(
        tmp_path,
        [{"type": "live", "duration": 10, "url": "udp://x", "format": "rawvidio"}],
    )
    with pytest.raises(PlaylistError, match="format"):
        load(path)


def test_load_example_live():
    playlist = load(EXAMPLES / "playlist_live.json")
    slide = playlist.slides[0]
    assert isinstance(slide, LiveSlide)
    assert slide.url == "http://127.0.0.1:8080/stream.mjpg"
    assert slide.fps == 30.0


def test_schedule_parse(tmp_path):
    path = _write(tmp_path, [{
        "type": "text", "duration": 5, "text": "X",
        "desde": "08:00", "hasta": "22:00", "dias": ["lun", "vie"],
    }])
    slide = load(path).slides[0]
    assert isinstance(slide.schedule, Schedule)
    assert slide.schedule.dias == (0, 4)
    assert slide.schedule.active_at(datetime(2026, 9, 14, 9, 0))       # lunes
    assert not slide.schedule.active_at(datetime(2026, 9, 15, 9, 0))   # martes
    assert not slide.schedule.active_at(datetime(2026, 9, 14, 23, 0))  # fuera de hora


def test_schedule_sin_dias_es_todos(tmp_path):
    path = _write(tmp_path, [{
        "type": "color", "duration": 5, "color": "#000000",
        "desde": "08:00", "hasta": "22:00",
    }])
    slide = load(path).slides[0]
    assert slide.schedule.dias == tuple(range(7))
    assert DIAS[3] == "jue"


def test_schedule_nocturno_cruza_medianoche(tmp_path):
    path = _write(tmp_path, [{
        "type": "color", "duration": 5, "color": "#000000",
        "desde": "22:00", "hasta": "06:00",
    }])
    slide = load(path).slides[0]
    assert slide.schedule.active_at(datetime(2026, 9, 14, 23, 30))
    assert slide.schedule.active_at(datetime(2026, 9, 14, 5, 0))
    assert not slide.schedule.active_at(datetime(2026, 9, 14, 12, 0))


def test_schedule_sin_horario_es_siempre(tmp_path):
    path = _write(tmp_path, [{"type": "color", "duration": 5, "color": "#000000"}])
    assert load(path).slides[0].schedule is None


def test_load_example_horarios():
    playlist = load(EXAMPLES / "playlist_horarios.json")
    assert len(playlist.slides) == 3
    dia = datetime(2026, 9, 14, 12, 0)    # lunes mediodía
    noche = datetime(2026, 9, 14, 23, 0)
    textos_dia = [s.text for s in playlist.active_slides(dia) if isinstance(s, TextSlide)]
    textos_noche = [s.text for s in playlist.active_slides(noche) if isinstance(s, TextSlide)]
    assert textos_dia == ["ABIERTO"]
    assert textos_noche == ["CERRADO"]
    assert len(playlist.active_slides(dia)) == 2   # texto + reloj, siempre vigente


@pytest.mark.parametrize("extra", [
    {"desde": "08:00"},
    {"hasta": "22:00"},
    {"desde": "8:00", "hasta": "22:00"},
    {"desde": "08:00", "hasta": "25:00"},
    {"desde": "08:00", "hasta": "22:00", "dias": ["lunes"]},
    {"desde": "08:00", "hasta": "22:00", "dias": []},
])
def test_schedule_errores(tmp_path, extra):
    path = _write(tmp_path, [{"type": "color", "duration": 5, "color": "#000000", **extra}])
    with pytest.raises(PlaylistError):
        load(path)


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
