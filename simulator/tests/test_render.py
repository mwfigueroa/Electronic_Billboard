import json
from datetime import datetime
from pathlib import Path

from PIL import Image

from panel_sim.playlist import load
from panel_sim.render import parse_time, render

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
EXAMPLE = EXAMPLES / "playlist.json"
FIXED_NOW = datetime(2026, 9, 15, 12, 0, 0)


def test_render_all(tmp_path):
    playlist = load(EXAMPLE)
    written, depth, gamma = render(EXAMPLE, tmp_path, scale=2, now=FIXED_NOW)
    assert len(written) == len(playlist.slides)
    assert depth == playlist.display.depth
    assert gamma == playlist.display.gamma
    img = Image.open(written[0])
    assert img.size == (256 * 2, 128 * 2)


def test_render_single_slide_scale_one(tmp_path):
    written, _, _ = render(EXAMPLE, tmp_path, scale=1, slide_index=0, now=FIXED_NOW)
    assert len(written) == 1
    assert Image.open(written[0]).size == (256, 128)


def test_render_depth_override(tmp_path):
    written, depth, _ = render(EXAMPLE, tmp_path, scale=1, depth=4, now=FIXED_NOW)
    assert depth == 4
    assert len(written) > 0


def test_render_preview_matches_panel_gamma(tmp_path):
    """El preview debe mostrar la luz del panel: 64→54, 128→130, 192→194.

    Fija la cadena completa quantize (duty lineal) + to_display (re-codificado
    sRGB). Sin el re-codificado estos valores salían 8 / 58 / 140.
    """
    playlist = tmp_path / "grays.json"
    playlist.write_text(
        json.dumps(
            {
                "version": 1,
                "display": {"width": 8, "height": 4, "depth": 5, "gamma": 2.2},
                "slides": [
                    {"type": "color", "color": "#404040", "duration": 1},
                    {"type": "color", "color": "#808080", "duration": 1},
                    {"type": "color", "color": "#c0c0c0", "duration": 1},
                ],
            }
        ),
        encoding="utf-8",
    )
    written, _, _ = render(playlist, tmp_path / "out", scale=1, now=FIXED_NOW)
    for path, expected in zip(written, (54, 130, 194)):
        pixel = Image.open(path).getpixel((0, 0))[0]
        assert abs(pixel - expected) <= 3, f"{path.name}: {pixel} != {expected}"


def test_parse_time():
    assert parse_time("21:45:00") == datetime(1900, 1, 1, 21, 45, 0)
