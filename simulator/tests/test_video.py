import subprocess

import numpy as np
import pytest

from panel_sim.playlist import Display, Playlist, VideoSlide
from panel_sim.timeline import Timeline
from panel_sim.video import VideoError, VideoSource, ffmpeg_exe


def _ffmpeg_available() -> bool:
    try:
        ffmpeg_exe()
        return True
    except VideoError:
        return False


pytestmark = pytest.mark.skipif(not _ffmpeg_available(), reason="ffmpeg no disponible")


@pytest.fixture()
def sample_video(tmp_path):
    path = tmp_path / "sample.mp4"
    subprocess.run(
        [
            ffmpeg_exe(), "-v", "error", "-y",
            "-f", "lavfi", "-i", "testsrc=size=64x36:rate=10:duration=1",
            "-pix_fmt", "yuv420p", str(path),
        ],
        check=True,
    )
    return path


def test_frames_at_canvas_size(sample_video):
    source = VideoSource(sample_video, (256, 128), fps=10, loop=True)
    first = source.frame_at(0.0)
    later = source.frame_at(0.5)
    assert first.shape == (128, 256, 3)
    assert first.dtype == np.uint8
    assert first.flags.writeable  # una capa de composición debe poder escribir
    assert not np.array_equal(first, later)
    source.close()


def test_rewind_restarts(sample_video):
    source = VideoSource(sample_video, (256, 128), fps=10, loop=True)
    first = source.frame_at(0.2)
    source.frame_at(0.8)
    again = source.frame_at(0.2)
    np.testing.assert_array_equal(first, again)
    source.close()


def test_paused_repeats_frame_without_decoding(sample_video):
    source = VideoSource(sample_video, (256, 128), fps=10, loop=True)
    first = source.frame_at(0.3)
    assert source.frame_at(0.3) is first
    source.close()


def test_missing_file(tmp_path):
    with pytest.raises(VideoError, match="no existe"):
        VideoSource(tmp_path / "nada.mp4", (256, 128))


def test_timeline_plays_video(sample_video):
    playlist = Playlist(
        display=Display(width=256, height=128),
        slides=(VideoSlide(duration=2.0, path=sample_video, fps=10),),
        source=None,  # type: ignore[arg-type]
    )
    timeline = Timeline(playlist)
    first = timeline.frame_at(0, 0.0)
    later = timeline.frame_at(0, 0.5)
    assert first.shape == (128, 256, 3)
    assert not np.array_equal(first, later)
    assert timeline.close() == 1
    assert timeline.close() == 0
