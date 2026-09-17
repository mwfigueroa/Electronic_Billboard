import io
import json
import threading
import urllib.request

from PIL import Image

from content.playlist import load
from panel_sim.editor import EditorState, serve


def _playlist(path):
    path.write_text(json.dumps({
        "version": 1,
        "slides": [{"type": "text", "text": "HOLA", "duration": 5}],
    }), encoding="utf-8")


def test_editor_inicia_con_esqueleto_si_no_existe(tmp_path):
    state = EditorState(tmp_path / "nueva.json")
    assert state.error is None
    assert state.snapshot()["playlist"]["slides"][0]["text"] == "NUEVO"


def test_editor_estado_valido_e_invalido(tmp_path):
    path = tmp_path / "pl.json"
    _playlist(path)
    state = EditorState(path)
    assert state.error is None
    assert state.frame().shape == (128, 256, 3)
    assert state.frame().max() > 0

    # una playlist inválida se adopta para seguir editando, pero conserva el
    # último timeline válido y reporta el error
    error = state.set_playlist({"slides": [{"type": "text", "duration": 5}]})
    assert error is not None
    assert state.snapshot()["error"] == error
    assert state.frame().max() > 0

    assert "vacía" in state.set_playlist({"slides": []})


def test_editor_guarda_validado(tmp_path):
    path = tmp_path / "pl.json"
    _playlist(path)
    state = EditorState(path)
    state.set_playlist({
        "version": 1,
        "slides": [{"type": "color", "color": "#404040", "duration": 2}],
    })
    assert state.save() is None
    assert load(path).slides[0].type == "color"
    assert state.snapshot()["dirty"] is False

    state.set_playlist({"slides": []})       # inválida: no escribe
    assert state.save() is not None
    assert load(path).slides[0].type == "color"


def test_editor_upload(tmp_path):
    path = tmp_path / "pl.json"
    _playlist(path)
    state = EditorState(path)
    relative = state.upload("logo.png", b"\x89PNGdatos")
    assert relative == "imagenes/logo.png"
    assert (tmp_path / "imagenes" / "logo.png").read_bytes() == b"\x89PNGdatos"
    # videos a su propia carpeta, sin importar mayúsculas de la extensión
    assert state.upload("clip.MP4", b"mp4") == "videos/clip.MP4"
    assert (tmp_path / "videos" / "clip.MP4").read_bytes() == b"mp4"
    # nombres con ruta no escapan del directorio
    assert state.upload("../../etc/passwd", b"x") == "imagenes/passwd"


def test_editor_preview_no_se_rompe_si_falta_el_archivo(tmp_path):
    path = tmp_path / "pl.json"
    path.write_text(json.dumps({
        "version": 1,
        "display": {"width": 256, "height": 128, "depth": 5, "gamma": 2.2},
        "slides": [
            {"type": "image", "path": "imagenes/no-existe.png", "duration": 5},
            {"type": "video", "path": "videos/no-existe.mp4", "duration": 5},
        ],
    }), encoding="utf-8")
    state = EditorState(path)
    assert state.error is None          # el documento es válido…
    for slide in (0, 1):
        frame = state.frame(slide=slide)   # …pero el archivo no está
        assert frame.shape == (128, 256, 3)
        assert frame.max() > 0             # placeholder, no excepción


def test_editor_http(tmp_path):
    path = tmp_path / "pl.json"
    _playlist(path)
    state = EditorState(path)
    server = serve(state, "127.0.0.1", 0)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"
    try:
        with urllib.request.urlopen(f"{base}/", timeout=5) as resp:
            html = resp.read()
        assert b"Editor de playlist" in html

        with urllib.request.urlopen(f"{base}/api/playlist", timeout=5) as resp:
            data = json.loads(resp.read())
        assert data["playlist"]["slides"][0]["text"] == "HOLA"

        request = urllib.request.Request(
            f"{base}/api/save", method="POST", data=b"{}",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=5) as resp:
            result = json.loads(resp.read())
        assert result["ok"] is True
        assert load(path).slides[0].text == "HOLA"

        request = urllib.request.Request(
            f"{base}/api/upload", method="POST", data=b"PNG",
            headers={"X-Filename": "x.png"},
        )
        with urllib.request.urlopen(request, timeout=5) as resp:
            result = json.loads(resp.read())
        assert result["path"] == "imagenes/x.png"

        for url in (f"{base}/preview.mjpg", f"{base}/preview.mjpg?slide=0"):
            with urllib.request.urlopen(url, timeout=5) as resp:
                head = resp.read(80)
            assert head.startswith(b"--frame")
            assert b"image/jpeg" in head

        request = urllib.request.Request(
            f"{base}/api/playlist", method="POST",
            data=json.dumps({"slides": []}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=5) as resp:
            result = json.loads(resp.read())
        assert result["ok"] is False
        assert "vacía" in result["error"]
    finally:
        server.shutdown()
        server.server_close()
