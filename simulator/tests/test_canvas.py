import numpy as np
import pytest
from PIL import Image

from panel_sim.canvas import (
    contain,
    hex_to_rgb,
    new_canvas,
    resolve_font,
    scale_with_grid,
    text_image,
)


def test_hex_to_rgb():
    assert hex_to_rgb("#ff8000") == (255, 128, 0)
    assert hex_to_rgb("#f80") == (255, 136, 0)
    assert hex_to_rgb("00ff00") == (0, 255, 0)


@pytest.mark.parametrize("bad", ["#12345", "#zzzzzz", "", "rojo"])
def test_hex_to_rgb_invalid(bad):
    with pytest.raises(ValueError):
        hex_to_rgb(bad)


def test_new_canvas_fill():
    canvas = new_canvas(4, 3, (1, 2, 3))
    assert canvas.size == (4, 3)
    assert np.all(np.asarray(canvas) == (1, 2, 3))


def test_text_image_has_pixels():
    img = text_image("A", "DejaVuSans-Bold", 16, (255, 255, 255))
    assert img.mode == "RGBA"
    alpha = np.asarray(img)[:, :, 3]
    assert alpha.max() == 255
    assert (alpha > 0).sum() > 10


def test_text_image_multiline():
    one = text_image("A", "DejaVuSans-Bold", 16, (255, 255, 255))
    two = text_image("A\nA", "DejaVuSans-Bold", 16, (255, 255, 255))
    assert two.height > one.height
    assert two.width == one.width


def test_resolve_font_unknown():
    with pytest.raises(FileNotFoundError):
        resolve_font("NoExiste-42")


def test_contain_no_upscale():
    small = Image.new("RGB", (8, 8))
    assert contain(small, 256, 128).size == (8, 8)


def test_contain_downscale_keeps_aspect():
    big = Image.new("RGB", (1024, 256))
    out = contain(big, 256, 128)
    assert out.width <= 256 and out.height <= 128
    assert out.width / out.height == pytest.approx(4.0, rel=0.01)


def test_contain_height_only_for_scroll():
    wide = Image.new("RGB", (800, 60))
    assert contain(wide, 256, 128, limit_width=False).size == (800, 60)
    tall = Image.new("RGB", (400, 400))
    assert contain(tall, 256, 128, limit_width=False).size == (128, 128)


def test_scale_with_grid_size():
    img = Image.new("RGB", (4, 3), (255, 0, 0))
    out = scale_with_grid(img, 4)
    assert out.size == (16, 12)
    assert scale_with_grid(img, 1) is img
