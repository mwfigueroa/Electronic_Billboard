"""Fuente de video para el simulador.

Decodifica con ffmpeg (del sistema o el binario estático de ``imageio-ffmpeg``)
a RGB24 por pipe, escalado y centrado (letterbox negro) al tamaño del canvas y
a una tasa fija. La lectura es secuencial — el visor pide tiempos crecientes —
y el pipe se reinicia solo si el tiempo retrocede (rebobinado o reinicio de
slide). Con ``loop`` el video se repite indefinidamente; sin él, al terminar
queda el último cuadro.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np


class VideoError(RuntimeError):
    """ffmpeg no disponible o video ilegible."""


def ffmpeg_exe() -> str:
    """Ruta a ffmpeg: el del sistema o el estático de ``imageio-ffmpeg``."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise VideoError(
            "ffmpeg no encontrado: instalar en el sistema (apt install ffmpeg) "
            "o el binario estático (pip install imageio-ffmpeg)"
        ) from exc
    return imageio_ffmpeg.get_ffmpeg_exe()


class VideoSource:
    """Cuadros RGB del video, al tamaño del canvas y a ``fps`` constante."""

    def __init__(
        self,
        path: str | Path,
        size: tuple[int, int],
        *,
        fps: float = 30.0,
        loop: bool = True,
    ):
        self.path = Path(path)
        if not self.path.exists():
            raise VideoError(f"no existe el video: {self.path}")
        self.size = (int(size[0]), int(size[1]))
        self.fps = float(fps)
        self.loop = bool(loop)
        self._proc: subprocess.Popen | None = None
        self._frames_read = 0
        self._current = -1
        self._last: np.ndarray | None = None
        self._eof = False

    def _start(self) -> None:
        width, height = self.size
        command = [ffmpeg_exe(), "-v", "error", "-nostdin"]
        if self.loop:
            command += ["-stream_loop", "-1"]
        command += [
            "-i", str(self.path),
            "-vf",
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
            "-r", f"{self.fps:g}",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ]
        try:
            self._proc = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )
        except OSError as exc:
            raise VideoError(f"no se pudo ejecutar ffmpeg: {exc}") from exc
        self._frames_read = 0
        self._current = -1
        self._eof = False

    def _read(self) -> np.ndarray | None:
        width, height = self.size
        assert self._proc is not None and self._proc.stdout is not None
        raw = self._proc.stdout.read(width * height * 3)
        if not raw or len(raw) < width * height * 3:
            self._eof = True
            return None
        frame = np.frombuffer(raw, dtype=np.uint8).reshape(height, width, 3).copy()
        self._current = self._frames_read
        self._frames_read += 1
        return frame

    def frame_at(self, t: float) -> np.ndarray:
        """Cuadro en el segundo ``t`` del video."""
        target = max(0, int(t * self.fps))
        if self._last is not None and target == self._current:
            return self._last
        if self._eof and self._last is not None and target >= self._frames_read:
            return self._last
        if self._proc is None or target < self._current:
            self.close()
            self._start()
        while self._frames_read <= target:
            frame = self._read()
            if frame is None:
                break
            self._last = frame
        if self._last is not None:
            return self._last
        return np.zeros((self.size[1], self.size[0], 3), dtype=np.uint8)

    def close(self) -> None:
        if self._proc is None:
            return
        if self._proc.stdout is not None:
            self._proc.stdout.close()
        self._proc.terminate()
        try:
            self._proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self._proc.kill()
        self._proc = None
