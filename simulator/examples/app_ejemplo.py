"""App de ejemplo del contrato de wire v1 (docs/14).

Publica frames RGB888 de 256×128 por MJPEG/HTTP. Cualquier aplicación que
hable el contrato puede reemplazarla: el panel —el mismo visor del simulador—
la consume con un slide `live`. No sabe nada de LED, gamma ni profundidad de
color: eso queda del lado del panel.

Uso:
    python examples/app_ejemplo.py                      # 127.0.0.1:8080
    .venv/bin/python -m panel_sim.viewer examples/playlist_live.json
"""

from __future__ import annotations

import argparse
import io
import math
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from PIL import Image, ImageDraw, ImageFont

W, H = 256, 128

_FONT_PATHS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def _font(size: int):
    for path in _FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_frame(t: float, n: int) -> Image.Image:
    """Un frame del contenido. Cualquier cosa dibujada acá es el 'contenido'."""
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # fondo con gradiente vertical
    for y in range(H):
        draw.line([(0, y), (W, y)], fill=(12, 22, 30 + int(90 * y / H)))

    # barra que rebota (movimiento claro a 256×128)
    x = int((W - 44) * (0.5 + 0.5 * math.sin(t * 1.6)))
    draw.rectangle([x, H - 30, x + 44, H - 16], fill=(0, 210, 130))

    # sol que respira
    r = int(10 + 3 * math.sin(t * 2.0))
    cx, cy = W - 34, 34
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 220, 90))

    # reloj y contador
    draw.text((8, 6), datetime.now().strftime("%H:%M:%S"), font=_font(30), fill=(255, 255, 255))
    draw.text((10, H - 16), f"contrato v1 · frame {n}", font=_font(11), fill=(150, 160, 170))

    return img


class MJPEGHandler(BaseHTTPRequestHandler):
    fps = 30.0

    def do_GET(self) -> None:  # noqa: N802 (interfaz de http.server)
        if self.path == "/":
            body = b"contrato de wire v1: stream MJPEG en /stream.mjpg\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path != "/stream.mjpg":
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        t0 = time.monotonic()
        next_t = t0
        n = 0
        try:
            while True:
                frame = render_frame(time.monotonic() - t0, n)
                buf = io.BytesIO()
                frame.save(buf, "JPEG", quality=85)
                data = buf.getvalue()

                self.wfile.write(b"--frame\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(b"Content-Length: " + str(len(data)).encode() + b"\r\n\r\n")
                self.wfile.write(data)
                self.wfile.write(b"\r\n")

                n += 1
                next_t += 1.0 / self.fps
                delay = next_t - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
                else:
                    next_t = time.monotonic()
        except (BrokenPipeError, ConnectionResetError):
            return

    def log_message(self, *args) -> None:
        pass   # sin ruido por cada request


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="app_ejemplo",
        description="Publica el contrato de wire v1 (MJPEG/HTTP) para el panel.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--fps", type=float, default=30.0)
    args = parser.parse_args(argv)

    MJPEGHandler.fps = args.fps
    server = ThreadingHTTPServer((args.host, args.port), MJPEGHandler)
    print(f"contrato de wire v1 → http://{args.host}:{args.port}/stream.mjpg ({args.fps:g} fps)")
    print("panel:  .venv/bin/python -m panel_sim.viewer examples/playlist_live.json")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
