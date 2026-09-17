"""Los clips de ejemplo: letras, movimiento y cuadros deterministas."""

import numpy as np

from content.clips import CLIPS, DURATION, FPS, HEIGHT, WIDTH, frame_at


def test_clips_deterministas_con_movimiento():
    for clip in CLIPS:
        frames = [frame_at(t, clip) for t in (0.5, 3.4, 5.2, 7.5, 9.8)]
        for frame in frames:
            assert frame.shape == (HEIGHT, WIDTH, 3)
            assert frame.max() > 0                 # nunca negra
        # cambia entre escenas y también dentro de una misma escena
        assert not np.array_equal(frames[0], frames[1])
        assert not np.array_equal(frames[3], frames[4])
    assert DURATION > 0 and FPS > 0
