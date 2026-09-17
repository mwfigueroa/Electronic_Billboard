"""Editor de playlist con preview en vivo (herramienta del lado panel).

Servidor local sin dependencias: lista y edita los slides, valida en memoria,
previsualiza el pipeline real (gamma + cuantización) por MJPEG y guarda el
archivo. La app en ejecución recarga sola al ver el mtime cambiado, así que el
circuito editor → app → panel queda cerrado sin reiniciar nada.

Es una herramienta del lado panel (como el visor y el render): consume la
playlist del lado app y muestra lo que el panel haría. El preview no dibuja la
máscara de LED ni emula distancia — para eso está el visor.

Uso:
    python -m panel_sim.editor examples/playlist.json
    (abrir http://127.0.0.1:8090)
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

from content.canvas import new_canvas, paste_aligned, text_image
from content.playlist import DEFAULT_FONT, PlaylistError, parse
from content.timeline import Timeline
from content.video import VideoError

from .quantize import quantize, to_display

PREVIEW_FPS = 10.0
DEFAULT_SIZE = (256, 128)
VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".m4v", ".mkv", ".avi"}
_PREVIEW_ERRORS = (PlaylistError, VideoError, OSError, ValueError)
SKELETON = {
    "version": 1,
    "display": {
        "width": 256, "height": 128, "depth": 5, "gamma": 2.2, "background": "#000000",
    },
    "slides": [{"type": "text", "text": "NUEVO", "size": 24, "duration": 5}],
}


def _encode_jpeg(frame: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(frame).save(buf, "JPEG", quality=85)
    return buf.getvalue()


def _missing_frame(width: int, height: int) -> np.ndarray:
    """Placeholder visible: la ruta no existe (mejor que cortar el preview)."""
    canvas = new_canvas(width, height, (40, 0, 0))
    img = text_image(
        "FALTA ARCHIVO", DEFAULT_FONT, max(10, height // 8), (255, 96, 96),
        align="center",
    )
    paste_aligned(canvas, img, "center", "middle")
    return np.asarray(canvas, dtype=np.uint8)


class EditorState:
    """Playlist en memoria, con preview y guardado validado.

    Un documento inválido se adopta (para poder seguir editando) pero se
    conserva el último timeline válido para el preview; el error se muestra.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.raw = self._read_initial()
        self.error: str | None = None
        self.dirty = False
        self._timeline: Timeline | None = None
        self._lock = threading.Lock()
        self._warned: set[str] = set()
        self._t0 = time.monotonic()
        self._apply(dirty=False)

    def _read_initial(self) -> dict:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raw = None
        if not isinstance(raw, dict):
            raw = json.loads(json.dumps(SKELETON))
        return raw

    def _apply(self, *, dirty: bool) -> str | None:
        self.dirty = dirty
        slides = self.raw.get("slides") if isinstance(self.raw, dict) else None
        if not slides:
            self.error = "la playlist está vacía: agregá al menos un slide"
            return self.error
        try:
            playlist = parse(self.raw, self.path.parent, source=self.path)
            self._timeline = Timeline(playlist)
            self.error = None
        except (PlaylistError, ValueError) as exc:
            self.error = str(exc)   # se conserva el timeline anterior
        return self.error

    def set_playlist(self, raw: object) -> str | None:
        """Valida y adopta una playlist nueva (sin tocar el disco)."""
        with self._lock:
            if not isinstance(raw, dict):
                self.error = "la playlist debe ser un objeto JSON"
                return self.error
            self.raw = raw
            return self._apply(dirty=True)

    def save(self) -> str | None:
        with self._lock:
            if self.error is not None:
                return self.error
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self.raw, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            self.dirty = False
            return None

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "path": str(self.path),
                "playlist": self.raw,
                "error": self.error,
                "dirty": self.dirty,
            }

    def depth_gamma(self) -> tuple[int, float]:
        display = self.raw.get("display", {}) if isinstance(self.raw, dict) else {}
        return int(display.get("depth", 5)), float(display.get("gamma", 2.2))

    def frame(self, slide: int | None = None) -> np.ndarray:
        with self._lock:
            timeline = self._timeline
        if timeline is None:
            return np.zeros((DEFAULT_SIZE[1], DEFAULT_SIZE[0], 3), dtype=np.uint8)
        now = datetime.now()
        t = time.monotonic() - self._t0
        try:
            if slide is not None and 0 <= slide < len(timeline.playlist.slides):
                chosen = timeline.playlist.slides[slide]
                return timeline.frame_at(slide, t % chosen.duration, now)
            return timeline.frame(t, now)
        except _PREVIEW_ERRORS as exc:
            # una ruta tipeada a mano que no existe no debe cortar el stream:
            # se muestra un placeholder y se avisa una vez por mensaje
            message = str(exc)
            if message not in self._warned:
                self._warned.add(message)
                print(f"preview: {message}")
            display = timeline.playlist.display
            return _missing_frame(display.width, display.height)

    def upload(self, filename: str, data: bytes) -> str:
        name = Path(filename).name or "archivo"
        folder = "videos" if Path(name).suffix.lower() in VIDEO_SUFFIXES else "imagenes"
        target = self.path.parent / folder / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return f"{folder}/{name}"


class EditorHandler(BaseHTTPRequestHandler):
    state: EditorState

    def _send(self, code: int, content_type: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj: object, code: int = 200) -> None:
        self._send(code, "application/json", json.dumps(obj).encode() + b"\n")

    def do_GET(self) -> None:  # noqa: N802 (interfaz de http.server)
        route, _, query = self.path.partition("?")
        if route == "/":
            html = Path(__file__).with_name("editor.html").read_bytes()
            self._send(200, "text/html; charset=utf-8", html)
        elif route == "/api/playlist":
            self._json(self.state.snapshot())
        elif route == "/preview.mjpg":
            slide = None
            for part in query.split("&"):
                if part.startswith("slide="):
                    try:
                        slide = int(part[6:])
                    except ValueError:
                        slide = None
            self._preview(slide)
        else:
            self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        if self.path == "/api/playlist":
            try:
                raw = json.loads(body)
            except json.JSONDecodeError as exc:
                self._json({"ok": False, "error": f"JSON inválido: {exc}"}, 400)
                return
            error = self.state.set_playlist(raw)
            self._json({"ok": error is None, "error": error})
        elif self.path == "/api/save":
            error = self.state.save()
            self._json({"ok": error is None, "error": error})
        elif self.path == "/api/upload":
            filename = self.headers.get("X-Filename", "imagen.png")
            path = self.state.upload(filename, body)
            self._json({"ok": True, "path": path})
        else:
            self.send_error(404)

    def _preview(self, slide: int | None) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            while True:
                frame = self.state.frame(slide)
                depth, gamma = self.state.depth_gamma()
                display = to_display(quantize(frame, depth, gamma), depth)
                jpeg = _encode_jpeg(display)
                self.wfile.write(b"--frame\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n")
                self.wfile.write(jpeg)
                self.wfile.write(b"\r\n")
                time.sleep(1.0 / PREVIEW_FPS)
        except (BrokenPipeError, ConnectionResetError):
            return

    def log_message(self, *args) -> None:
        pass


def serve(state: EditorState, host: str, port: int) -> ThreadingHTTPServer:
    """Servidor HTTP con el editor enganchado (reusable desde tests)."""
    handler = type("BoundEditorHandler", (EditorHandler,), {"state": state})
    return ThreadingHTTPServer((host, port), handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="panel_sim.editor",
        description="Editor de playlist con preview del pipeline del panel.",
    )
    parser.add_argument("playlist", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args(argv)

    state = EditorState(args.playlist)
    if state.error is not None:
        print(f"aviso: {state.error}")
    server = serve(state, args.host, args.port)
    print(f"editor: http://{args.host}:{args.port}")
    print(f"  playlist: {args.playlist}")
    print("  al guardar, la app recarga sola (mtime) y el panel lo muestra")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
