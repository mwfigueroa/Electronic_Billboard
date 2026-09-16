"""Vínculo directo app → panel por socket Unix (misma máquina).

Transporte local para desarrollo: los cuadros RGB888 viajan crudos, sin códec
ni ffmpeg, así que el panel recibe bit a bit lo que la app compuso — es el
camino de mayor fidelidad y el más barato en CPU. No reemplaza al contrato de
red ([`docs/14`](../../docs/14_software_contenido.md)): solo funciona con app
y panel en la misma máquina.

El sentido de la conexión es el mismo que en MJPEG: **el panel inicia**. La app
escucha en un socket Unix; al conectar manda un encabezado ASCII
(``BILLBOARD/1 RAW 256x128 rgb24\n``) y después cuadros de ``w·h·3`` bytes uno
tras otro. Si el panel se atrasa, la app no acumula: siempre publica el último
cuadro, y el panel reencuadra descartando cuadros enteros.
"""

from __future__ import annotations

import select
import socket
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np

HEADER_PREFIX = b"BILLBOARD/1 RAW "
MAX_BUFFER_FRAMES = 8


def _header(width: int, height: int) -> bytes:
    return HEADER_PREFIX + f"{width}x{height} rgb24\n".encode()


def path_from_url(url: str) -> Path:
    """``unix:/tmp/x.sock`` → ``/tmp/x.sock`` (tolera ``unix://`` y barras de más)."""
    return Path("/" + url.split("unix:", 1)[1].lstrip("/"))


class RawSocketServer:
    """Publica el último cuadro del publisher en un socket Unix."""

    def __init__(self, publisher, path: str | Path, *, fps: float = 30.0):
        self.publisher = publisher
        self.path = Path(path)
        self.fps = float(fps)
        self._server: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._closing = threading.Event()

    def start(self) -> None:
        if self.path.exists():
            probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                probe.connect(str(self.path))
            except OSError:
                self.path.unlink(missing_ok=True)   # socket huérfano
            else:
                raise RuntimeError(f"ya hay una app publicando en {self.path}")
            finally:
                probe.close()
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            server.bind(str(self.path))
        except OSError as exc:
            server.close()
            raise RuntimeError(f"no se pudo escuchar en {self.path}: {exc}") from exc
        server.listen(4)
        self._server = server
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()

    def _accept_loop(self) -> None:
        assert self._server is not None
        # con timeout, close() no tiene que esperar a que llegue una conexión
        self._server.settimeout(0.2)
        while not self._closing.is_set():
            try:
                conn, _ = self._server.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            conn.settimeout(None)   # bloqueante: el publisher marca el ritmo
            threading.Thread(
                target=self._client_loop, args=(conn,), daemon=True
            ).start()

    def _client_loop(self, conn: socket.socket) -> None:
        width, height = self.publisher.size
        last_sent: bytes | None = None
        try:
            conn.sendall(_header(width, height))
            while not self._closing.is_set():
                raw = self.publisher.raw()
                if raw is not None and raw != last_sent:
                    conn.sendall(raw)
                    last_sent = raw
                time.sleep(1.0 / (2 * self.fps))
        except OSError:
            pass
        finally:
            conn.close()

    def close(self) -> None:
        self._closing.set()
        if self._server is not None:
            self._server.close()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=1)
            self._thread = None
        self.path.unlink(missing_ok=True)


class RawSocketSource:
    """Cuadros RGB crudos de un socket Unix, con reconexión automática.

    Interfaz compatible con la parte viva de ``VideoSource``:
    ``frame_latest()`` devuelve el último cuadro (o negro si la app todavía no
    está) y ``close()`` corta. Reintenta la conexión cada ``retry_s``.
    """

    def __init__(
        self,
        url: str,
        size: tuple[int, int],
        *,
        fps: float = 30.0,
        retry_s: float = 2.0,
        warn: Callable[[str], None] | None = None,
    ):
        self.url = url
        self.path = path_from_url(url)
        self.size = (int(size[0]), int(size[1]))
        self.fps = float(fps)
        self.retry_s = float(retry_s)
        self._warn = warn or (lambda message: print(message, file=sys.stderr))
        self._sock: socket.socket | None = None
        self._buf = bytearray()
        self._last: np.ndarray | None = None
        self._retry_at = 0.0

    @property
    def _frame_bytes(self) -> int:
        return self.size[0] * self.size[1] * 3

    def _black(self) -> np.ndarray:
        return np.zeros((self.size[1], self.size[0], 3), dtype=np.uint8)

    def _connect(self) -> bool:
        if time.monotonic() < self._retry_at:
            return False
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        try:
            sock.connect(str(self.path))
            header = b""
            while not header.endswith(b"\n"):
                chunk = sock.recv(1)   # byte a byte: no robar bytes del cuadro
                if not chunk or len(header) > 256:
                    raise OSError("encabezado inválido")
                header += chunk
        except OSError:
            sock.close()
            self._retry_at = time.monotonic() + self.retry_s
            return False
        expected = f"{self.size[0]}x{self.size[1]}".encode()
        if not header.startswith(HEADER_PREFIX) or (
            header[len(HEADER_PREFIX):].split()[0] != expected
        ):
            self._warn(
                f"vínculo directo: {self.path} sirve "
                f"{header.decode(errors='replace').strip()!r}; "
                f"se esperaba {expected.decode()}"
            )
            sock.close()
            self._retry_at = time.monotonic() + self.retry_s
            return False
        sock.settimeout(0.5)
        self._sock = sock
        self._buf.clear()
        return True

    def _disconnect(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None
        self._retry_at = time.monotonic() + self.retry_s

    def _drain(self) -> None:
        assert self._sock is not None
        while True:
            ready, _, _ = select.select([self._sock], [], [], 0)
            if not ready:
                break
            try:
                chunk = self._sock.recv(65536)
            except TimeoutError:   # carrera entre select y recv
                break
            if not chunk:
                raise OSError("la app cerró el vínculo")
            self._buf.extend(chunk)
        while len(self._buf) >= self._frame_bytes:
            raw = bytes(self._buf[: self._frame_bytes])
            del self._buf[: self._frame_bytes]
            self._last = (
                np.frombuffer(raw, dtype=np.uint8)
                .reshape(self.size[1], self.size[0], 3)
                .copy()
            )
        if len(self._buf) > MAX_BUFFER_FRAMES * self._frame_bytes:
            # atraso grande: reencuadrar descartando cuadros enteros
            keep = len(self._buf) % self._frame_bytes
            del self._buf[: len(self._buf) - keep]

    def frame_latest(self) -> np.ndarray:
        if self._sock is None and not self._connect():
            return self._last if self._last is not None else self._black()
        try:
            self._drain()
        except OSError:
            self._disconnect()
        if self._last is not None:
            return self._last
        return self._black()

    def close(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None
