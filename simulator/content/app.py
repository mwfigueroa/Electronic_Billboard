"""App de contenido: publica la playlist como fuente viva (contrato v1).

Timeline + un loop + un publicador MJPEG. Respeta los horarios de la
playlist, recarga el archivo en caliente si cambia y expone ``/status`` para
supervisión (frames, errores, slide actual, antigüedad del último cuadro).

Además de MJPEG sirve el **vínculo directo** en un socket Unix (cuadros RGB
crudos, sin códec; ``rawlink.py``): el panel lo consume bit a bit cuando está
en la misma máquina.

Uso:
    python -m content.app examples/playlist.json --port 8080
    make app
Panel:
    make view PLAYLIST=examples/playlist_live.json      # por red (MJPEG)
    make view PLAYLIST=examples/playlist_directo.json   # vínculo directo
"""

from __future__ import annotations

import argparse
import io
import json
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
from PIL import Image

from .playlist import PlaylistError, load
from .rawlink import RawSocketServer
from .timeline import Timeline

DEFAULT_SIZE = (256, 128)


def _encode_jpeg(frame: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(frame).save(buf, "JPEG", quality=85)
    return buf.getvalue()


class Publisher:
    """Compone la playlist a JPEG y mantiene el estado para supervisión."""

    def __init__(self, playlist_path: str | Path, *, fps: float = 30.0):
        self.path = Path(playlist_path)
        self.fps = float(fps)
        self.started = time.monotonic()
        self.timeline: Timeline | None = None
        self.error: str | None = None
        self.frames = 0
        self.errors = 0
        self.last_frame_at: float | None = None
        self.raw_socket: str | None = None
        self._jpeg = _encode_jpeg(np.zeros((DEFAULT_SIZE[1], DEFAULT_SIZE[0], 3), dtype=np.uint8))
        self._raw: bytes | None = None
        self._lock = threading.Lock()
        self._playlist_mtime: float | None = None
        self._last_reload_check = 0.0
        self._load()

    # --- carga y recarga en caliente ---------------------------------------
    def _load(self) -> None:
        try:
            self._playlist_mtime = self.path.stat().st_mtime
        except OSError:
            self._playlist_mtime = None
        try:
            playlist = load(self.path)
            self.timeline = Timeline(playlist)
            self.error = None
            print(
                f"playlist: {self.path} · {len(playlist.slides)} slides · "
                f"{playlist.duration:.1f} s"
            )
        except (PlaylistError, ValueError, OSError) as exc:
            self.error = str(exc)
            print(f"error de playlist: {exc}")

    def reload_if_changed(self) -> bool:
        try:
            mtime = self.path.stat().st_mtime
        except OSError:
            mtime = None
        if mtime == self._playlist_mtime:
            return False
        print(f"recarga en caliente: {self.path}")
        old = self.timeline
        self._load()
        if self.timeline is not None and old is not None and old is not self.timeline:
            old.close()
        return True

    # --- producción de frames ------------------------------------------------
    @property
    def size(self) -> tuple[int, int]:
        """Tamaño del canvas publicado (el que anuncia el vínculo directo)."""
        if self.timeline is not None:
            display = self.timeline.playlist.display
            return display.width, display.height
        return DEFAULT_SIZE

    def _blank(self) -> np.ndarray:
        if self.timeline is not None:
            display = self.timeline.playlist.display
            return np.zeros((display.height, display.width, 3), dtype=np.uint8)
        return np.zeros((DEFAULT_SIZE[1], DEFAULT_SIZE[0], 3), dtype=np.uint8)

    def step(self) -> None:
        """Compone y publica un frame. Nunca levanta: un error suma y sigue."""
        try:
            if self.timeline is None:
                frame = self._blank()
            else:
                frame = self.timeline.frame(time.monotonic() - self.started)
            jpeg = _encode_jpeg(frame)
            raw = np.ascontiguousarray(frame).tobytes()
            with self._lock:
                self._jpeg = jpeg
                self._raw = raw
                self.frames += 1
                self.last_frame_at = time.monotonic()
        except Exception as exc:   # noqa: BLE001 — la app no se cae por un cuadro
            self.errors += 1
            print(f"error de composición: {exc}")

    def run(self) -> None:
        """Loop de publicación a ``fps`` con chequeo de recarga cada segundo."""
        next_t = time.monotonic()
        while True:
            self.step()
            next_t += 1.0 / self.fps
            delay = next_t - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            else:
                next_t = time.monotonic()
            if time.monotonic() - self._last_reload_check > 1.0:
                self._last_reload_check = time.monotonic()
                self.reload_if_changed()

    # --- estado --------------------------------------------------------------
    def jpeg(self) -> bytes:
        with self._lock:
            return self._jpeg

    def raw(self) -> bytes | None:
        """Último cuadro RGB888 crudo (None hasta el primer ``step``)."""
        with self._lock:
            return self._raw

    def status(self) -> dict:
        with self._lock:
            frames = self.frames
            errors = self.errors
            last = self.last_frame_at
            size = len(self._jpeg)
        now = datetime.now()
        playlist = self.timeline.playlist if self.timeline is not None else None
        active = playlist.active_slides(now) if playlist is not None else ()
        found = (
            self.timeline.locate(time.monotonic() - self.started, now)
            if self.timeline is not None
            else None
        )
        return {
            "ok": self.error is None and last is not None,
            "uptime_s": round(time.monotonic() - self.started, 1),
            "frames": frames,
            "errors": errors,
            "fps_target": self.fps,
            "last_frame_age_s": round(time.monotonic() - last, 2) if last else None,
            "jpeg_bytes": size,
            "playlist": str(self.path),
            "playlist_error": self.error,
            "raw_socket": self.raw_socket,
            "slides_total": len(playlist.slides) if playlist is not None else 0,
            "slides_active": len(active),
            "current_slide": found[0] if found else None,
            "current_type": (
                playlist.slides[found[0]].type
                if playlist is not None and found is not None
                else None
            ),
        }


class AppHandler(BaseHTTPRequestHandler):
    publisher: Publisher
    fps: float = 30.0

    def _send(self, code: int, content_type: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (interfaz de http.server)
        if self.path == "/":
            self._send(200, "text/plain; charset=utf-8", (
                "app de contenido · contrato de wire v1 (docs/14)\n"
                "/stream.mjpg  stream MJPEG\n"
                "/status       estado JSON\n"
            ).encode())
        elif self.path == "/status":
            self._send(200, "application/json", (
                json.dumps(self.publisher.status(), indent=2) + "\n"
            ).encode())
        elif self.path == "/stream.mjpg":
            self._stream()
        else:
            self.send_error(404)

    def _stream(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        last_sent = b""
        try:
            while True:
                jpeg = self.publisher.jpeg()
                if jpeg and jpeg != last_sent:
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n")
                    self.wfile.write(jpeg)
                    self.wfile.write(b"\r\n")
                    last_sent = jpeg
                time.sleep(1.0 / (2 * self.fps))
        except (BrokenPipeError, ConnectionResetError):
            return

    def log_message(self, *args) -> None:
        pass


def serve(publisher: Publisher, host: str, port: int, *, fps: float = 30.0) -> ThreadingHTTPServer:
    """Servidor HTTP con el publisher enganchado (reusable desde tests)."""
    handler = type("BoundAppHandler", (AppHandler,), {"publisher": publisher, "fps": fps})
    return ThreadingHTTPServer((host, port), handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="content.app",
        description="Publica una playlist como fuente viva del contrato v1.",
    )
    parser.add_argument("playlist", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--raw-socket", default="/tmp/billboard.sock",
                        help="socket Unix del vínculo directo (vacío = desactivado)")
    parser.add_argument("--no-stream", action="store_true",
                        help="solo componer (sin servidor); para pruebas")
    args = parser.parse_args(argv)

    publisher = Publisher(args.playlist, fps=args.fps)
    if args.no_stream:
        publisher.run()
        return 0

    raw_server = None
    if args.raw_socket:
        raw_server = RawSocketServer(publisher, args.raw_socket, fps=args.fps)
        try:
            raw_server.start()
        except RuntimeError as exc:
            print(f"aviso: vínculo directo desactivado: {exc}")
            raw_server = None
        else:
            publisher.raw_socket = str(raw_server.path)

    server = serve(publisher, args.host, args.port, fps=args.fps)
    producer = threading.Thread(target=publisher.run, daemon=True)
    producer.start()

    print("app de contenido · contrato de wire v1 (docs/14)")
    print(f"  stream: http://{args.host}:{args.port}/stream.mjpg")
    print(f"  estado: http://{args.host}:{args.port}/status")
    if raw_server is not None:
        print(f"  directo: unix:{raw_server.path} (make view PLAYLIST=examples/playlist_directo.json)")
    else:
        print("  panel:  make view PLAYLIST=examples/playlist_live.json")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if raw_server is not None:
            raw_server.close()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
