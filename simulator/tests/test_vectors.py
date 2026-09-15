import json

import numpy as np

from panel_sim.bitplanes import (
    bitplanes_to_rgb,
    canonical_test_frame,
    rgb_to_bitplanes,
)
from panel_sim.quantize import quantize
from panel_sim.vectors import write_vectors


def test_write_vectors(tmp_path):
    width, height, depth = 16, 8, 5
    written = write_vectors(tmp_path, width=width, height=height, depth=depth)
    assert len(written) == depth * 3 + 4
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "expected_levels.json").exists()
    assert (tmp_path / "frame_rgb888.mem").exists()
    assert (tmp_path / "gamma_lut_2p2_5b.mem").exists()


def test_frame_file_matches_pattern(tmp_path):
    width, height, depth = 16, 8, 5
    write_vectors(tmp_path, width=width, height=height, depth=depth)
    lines = (tmp_path / "frame_rgb888.mem").read_text().splitlines()
    assert len(lines) == width * height
    frame = canonical_test_frame(width, height)
    for n, line in enumerate(lines):
        y, x = divmod(n, width)
        r, g, b = frame[y, x]
        assert line == f"{int(r):02x}{int(g):02x}{int(b):02x}"


def test_gamma_lut_matches_quantize(tmp_path):
    write_vectors(tmp_path, depth=5, gamma=2.2)
    lines = (tmp_path / "gamma_lut_2p2_5b.mem").read_text().splitlines()
    assert len(lines) == 256
    ramp = np.arange(256, dtype=np.uint8).reshape(256, 1, 1).repeat(3, axis=2)
    expected = quantize(ramp, 5, 2.2)[:, 0, 0]
    assert [int(line, 16) for line in lines] == [int(v) for v in expected]


def test_mem_files_match_bitplanes(tmp_path):
    width, height, depth = 16, 8, 5
    write_vectors(tmp_path, width=width, height=height, depth=depth)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    levels = json.loads((tmp_path / "expected_levels.json").read_text())

    r = np.array(levels["r"], dtype=np.uint8)
    g = np.array(levels["g"], dtype=np.uint8)
    b = np.array(levels["b"], dtype=np.uint8)
    planes = rgb_to_bitplanes(np.stack([r, g, b], axis=-1), depth)

    for bit in range(depth):
        for channel, name in enumerate("rgb"):
            path = tmp_path / manifest["files"][f"b{bit}_{name}"]
            rows = path.read_text().splitlines()
            assert len(rows) == height
            for y, row in enumerate(rows):
                value = int(row, 16)
                for x in range(width):
                    assert (value >> x) & 1 == planes[bit, channel, y, x]


def test_expected_levels_reconstruct(tmp_path):
    width, height, depth, gamma = 16, 8, 5, 2.2
    write_vectors(tmp_path, width=width, height=height, depth=depth, gamma=gamma)
    levels = quantize(canonical_test_frame(width, height), depth, gamma)
    data = json.loads((tmp_path / "expected_levels.json").read_text())
    np.testing.assert_array_equal(np.array(data["r"], dtype=np.uint8), levels[:, :, 0])
    np.testing.assert_array_equal(np.array(data["g"], dtype=np.uint8), levels[:, :, 1])
    np.testing.assert_array_equal(np.array(data["b"], dtype=np.uint8), levels[:, :, 2])
    assert bitplanes_to_rgb(rgb_to_bitplanes(levels, depth)).shape == (height, width, 3)
