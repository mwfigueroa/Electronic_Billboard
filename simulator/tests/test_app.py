import io
import json
import threading
import time
import urllib.request
from datetime import datetime, timedelta

import numpy as np
from PIL import Image

from content.app import Publisher, serve


def _write(path, slides):
    path.write_text(json.dumps({"version": 1, "slides": slides}), encoding="utf-8")


def test_publisher_status(tmp_path):
    playlist = tmp_path / "pl.json"
    _write(playlist, [{"type": "text", "duration": 5, "text": "HOLA"}])
    pub = Publisher(playlist, fps=60)
    for _ in range(5):
        pub.step()
    status = pub.status()
    assert status["ok"] is True
    assert status["frames"] == 5
    assert status["errors"] == 0
    assert status["slides_active"] == 1
    assert status["current_type"] == "text"
    assert status["jpeg_bytes"] > 500
    assert Image.open(io.BytesIO(pub.jpeg())).size == (256, 128)


def test_publisher_hot_reload(tmp_path):
    playlist = tmp_path / "pl.json"
    _write(playlist, [{"type": "text", "duration": 5, "text": "A"}])
    pub = Publisher(playlist, fps=60)
    pub.step()
    assert pub.status()["current_type"] == "text"

    time.sleep(0.02)
    _write(playlist, [{"type": "color", "duration": 5, "color": "#404040"}])
    assert pub.reload_if_changed() is True
    pub.step()
    assert pub.status()["current_type"] == "color"
    assert pub.reload_if_changed() is False


def test_publisher_reload_roto_conserva_la_anterior(tmp_path):
    playlist = tmp_path / "pl.json"
    _write(playlist, [{"type": "color", "duration": 5, "color": "#404040"}])
    pub = Publisher(playlist, fps=60)
    pub.step()

    time.sleep(0.02)
    playlist.write_text("{ roto", encoding="utf-8")
    assert pub.reload_if_changed() is True
    assert pub.status()["playlist_error"] is not None
    pub.step()
    assert pub.status()["current_type"] == "color"   # siguió con la anterior


def test_publisher_sin_programa_publica_negro(tmp_path):
    now = datetime.now()
    playlist = tmp_path / "pl.json"
    _write(playlist, [{
        "type": "text", "duration": 5, "text": "X",
        "desde": (now + timedelta(minutes=1)).strftime("%H:%M"),
        "hasta": (now + timedelta(minutes=2)).strftime("%H:%M"),
    }])
    pub = Publisher(playlist, fps=60)
    pub.step()
    status = pub.status()
    assert status["slides_active"] == 0
    assert status["current_slide"] is None
    img = np.asarray(Image.open(io.BytesIO(pub.jpeg())))
    assert img.max() == 0   # todo negro


def test_http_endpoints(tmp_path):
    playlist = tmp_path / "pl.json"
    _write(playlist, [{"type": "color", "duration": 5, "color": "#204080"}])
    pub = Publisher(playlist, fps=60)
    pub.step()

    server = serve(pub, "127.0.0.1", 0, fps=60)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{port}"
        with urllib.request.urlopen(f"{base}/status", timeout=5) as resp:
            status = json.loads(resp.read())
        assert status["frames"] >= 1
        assert status["current_type"] == "color"

        with urllib.request.urlopen(f"{base}/", timeout=5) as resp:
            assert b"contrato" in resp.read()

        with urllib.request.urlopen(f"{base}/stream.mjpg", timeout=5) as resp:
            head = resp.read(80)
        assert head.startswith(b"--frame")
        assert b"image/jpeg" in head
    finally:
        server.shutdown()
        server.server_close()
