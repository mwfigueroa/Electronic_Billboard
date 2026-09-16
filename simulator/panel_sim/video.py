"""Fuente de video para el simulador (archivos, streams y captura X11).

Decodifica con ffmpeg (del sistema o el binario estático de ``imageio-ffmpeg``)
a RGB24 por pipe, escalado y centrado (letterbox negro) al tamaño del canvas y
a una tasa fija.

Dos modos:

- **Archivo** (``VideoSource``): lectura secuencial con reinicio si el tiempo
  retrocede (rebobinado o reinicio de slide).
- **Viva** (``live=True``, contrato de wire v1 de docs/14): descarta atrasos y
  devuelve siempre el último cuadro disponible; si el stream se corta,
  reintenta la conexión cada 2 s (útil mientras se reinicia la app que
  publica).
"""

from __future__ import annotations

import select
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np


class VideoError(RuntimeError):
    """ffmpeg no disponible o fuente ilegible."""


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
    """Cuadros RGB de la fuente, al tamaño del canvas y a ``fps`` constante."""

    def __init__(
        self,
        source: str | Path,
        size: tuple[int, int],
        *,
        fps: float = 30.0,
        loop: bool = True,
        input_args: tuple[str, ...] = (),
        live: bool = False,
    ):
        self.source = str(source)
        self.is_local = "://" not in self.source and not self.source.startswith(":")
        if self.is_local and not Path(self.source).exists():
            raise VideoError(f"no existe el video: {self.source}")
        self.size = (int(size[0]), int(size[1]))
        self.fps = float(fps)
        self.loop = bool(loop)
        self.input_args = tuple(input_args)
        self.live = bool(live)
        self._proc: subprocess.Popen | None = None
        self._frames_read = 0
        self._current = -1
        self._last: np.ndarray | None = None
        self._eof = False
        self._eof_at = 0.0
        self._first_frame_at = time.monotonic() + 2.0

    def _start(self) -> None:
        width, height = self.size
        command = [ffmpeg_exe(), "-v", "error", "-nostdin"]
        if self.live and len(self.input_args) >= 2 and self.input_args[0] == "-f" \
                and self.input_args[1] in ("x11grab", "v4l2", "mjpeg"):
            # baja latencia donde el demuxer bufferea; con rawvideo nobuffer
            # descarta el único cuadro de un archivo (verificado)
            command += ["-fflags", "nobuffer", "-flags", "low_delay"]
        elif not self.live and self.loop:
            command += ["-stream_loop", "-1"]
        command += list(self.input_args)
        command += [
            "-i", self.source,
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
            self._eof_at = time.monotonic()
            return None
        frame = np.frombuffer(raw, dtype=np.uint8).reshape(height, width, 3).copy()
        self._current = self._frames_read
        self._frames_read += 1
        return frame

    def _data_available(self) -> bool:
        assert self._proc is not None and self._proc.stdout is not None
        ready, _, _ = select.select([self._proc.stdout], [], [], 0)
        return bool(ready)

    def frame_at(self, t: float) -> np.ndarray:
        """Cuadro en el segundo ``t`` de la fuente (modo archivo)."""
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

    def frame_latest(self) -> np.ndarray:
        """Último cuadro disponible (modo vivo): descarta atrasos."""
        if self._eof and self.live and time.monotonic() - self._eof_at > 2.0:
            self.close()
        if self._proc is None:
            self._start()

        # espera acotada del primer cuadro: ffmpeg tarda en arrancar y la app
        # puede todavía no estar publicando. Después no se bloquea más.
        if self._last is None:
            while time.monotonic() < self._first_frame_at and not self._eof:
                assert self._proc is not None and self._proc.stdout is not None
                ready, _, _ = select.select([self._proc.stdout], [], [], 0.05)
                if not ready:
                    continue
                frame = self._read()
                if frame is not None:
                    self._last = frame
                break

        for _ in range(8):   # tope por llamada para no monopolizar el render
            if not self._data_available():
                break
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
