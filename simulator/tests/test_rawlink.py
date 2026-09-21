"""Tests del vínculo directo app → panel (socket Unix crudo)."""

import json
import time

import pytest

from content.app import Publisher
from content.playlist import load
from content.rawlink import RawSocketServer, RawSocketSource, path_from_url
from content.timeline import Timeline


def _playlist(path, color="#204060"):
    path.write_text(json.dumps({
        "version": 1,
        "display": {"width": 256, "height": 128, "depth": 5, "gamma": 2.2},
        "slides": [{"type": "color", "color": color, "duration": 60}],
    }), encoding="utf-8")
    return path


def test_path_from_url():
    assert str(path_from_url("unix:/tmp/x.sock")) == "/tmp/x.sock"
    assert str(path_from_url("unix:///tmp/x.sock")) == "/tmp/x.sock"


def test_entrega_el_cuadro_bit_a_bit(tmp_path):
    publisher = Publisher(_playlist(tmp_path / "pl.json"))
    publisher.step()
    sock = tmp_path / "panel.sock"
    server = RawSocketServer(publisher, sock)
    server.start()
    source = RawSocketSource(f"unix:{sock}", (256, 128))
    try:
        frame = source.frame_latest()
        assert frame.shape == (128, 256, 3)
        assert frame.tobytes() == publisher.raw()   # sin códec de por medio
        assert frame.max() > 0
    finally:
        source.close()
        server.close()
    assert not sock.exists()


def test_sin_app_devuelve_negro_y_reconecta(tmp_path):
    publisher = Publisher(_playlist(tmp_path / "pl.json"))
    publisher.step()
    sock = tmp_path / "panel.sock"
    source = RawSocketSource(f"unix:{sock}", (256, 128), retry_s=0.05)
    try:
        blank = source.frame_latest()
        assert blank.shape == (128, 256, 3)
        assert blank.max() == 0

        server = RawSocketServer(publisher, sock)
        server.start()
        try:
            deadline = time.monotonic() + 5
            frame = source.frame_latest()
            while frame.max() == 0 and time.monotonic() < deadline:
                time.sleep(0.05)
                frame = source.frame_latest()
            assert frame.tobytes() == publisher.raw()
        finally:
            server.close()
    finally:
        source.close()


def test_tamano_incorrecto_avisa_y_sigue_negro(tmp_path):
    publisher = Publisher(_playlist(tmp_path / "pl.json"))
    publisher.step()
    sock = tmp_path / "panel.sock"
    server = RawSocketServer(publisher, sock)
    server.start()
    messages: list[str] = []
    source = RawSocketSource(
        f"unix:{sock}", (128, 64), retry_s=0.05, warn=messages.append
    )
    try:
        frame = source.frame_latest()
        assert frame.shape == (64, 128, 3)
        assert frame.max() == 0
        assert any("256x128" in message for message in messages)
    finally:
        source.close()
        server.close()


def test_segunda_app_en_el_mismo_socket_falla(tmp_path):
    publisher = Publisher(_playlist(tmp_path / "pl.json"))
    publisher.step()
    sock = tmp_path / "panel.sock"
    server = RawSocketServer(publisher, sock)
    server.start()
    try:
        with pytest.raises(RuntimeError):
            RawSocketServer(publisher, sock).start()
    finally:
        server.close()


def test_socket_huerfano_se_recicla(tmp_path):
    publisher = Publisher(_playlist(tmp_path / "pl.json"))
    publisher.step()
    sock = tmp_path / "panel.sock"
    sock.write_bytes(b"")   # como deja un cierre abrupto
    server = RawSocketServer(publisher, sock)
    server.start()
    source = RawSocketSource(f"unix:{sock}", (256, 128))
    try:
        # el hilo del server manda el primer cuadro justo tras el encabezado;
        # si todavía no tuvo turno, frame_latest() devuelve negro: esperar
        limite = time.monotonic() + 2.0
        while time.monotonic() < limite:
            frame = source.frame_latest()
            if frame.tobytes() == publisher.raw():
                break
            time.sleep(0.02)
        assert frame.tobytes() == publisher.raw()
    finally:
        source.close()
        server.close()


def test_timeline_usa_el_vinculo_directo(tmp_path):
    path = tmp_path / "directo.json"
    path.write_text(json.dumps({
        "version": 1,
        "display": {"width": 256, "height": 128, "depth": 5, "gamma": 2.2},
        "slides": [{
            "type": "live", "url": "unix:/tmp/no-existe.sock",
            "fps": 30, "duration": 60,
        }],
    }), encoding="utf-8")
    timeline = Timeline(load(path))
    try:
        frame = timeline.frame_at(0, 0.0)   # sin app: negro, no explota
        assert frame.shape == (128, 256, 3)
        source = next(iter(timeline._videos.values()))
        assert isinstance(source, RawSocketSource)
        assert source.path.name == "no-existe.sock"
    finally:
        assert timeline.close() == 1
