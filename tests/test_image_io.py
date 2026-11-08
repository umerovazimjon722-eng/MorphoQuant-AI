import numpy as np
import pytest
from PIL import Image

from morphoquant.image_io import load_rgb_image


def test_load_rgb_image_returns_rgb_uint8_array(tmp_path):
    source = np.zeros((12, 18, 3), dtype=np.uint8)
    source[..., 0] = 120
    image_path = tmp_path / "synthetic.png"
    Image.fromarray(source, mode="RGB").save(image_path)

    loaded = load_rgb_image(image_path)

    assert loaded.shape == (12, 18, 3)
    assert loaded.dtype == np.uint8
    assert np.array_equal(loaded, source)


def test_load_rgb_image_raises_for_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_rgb_image(tmp_path / "missing.png")


def test_load_rgb_image_rejects_unreadable_file(tmp_path):
    invalid_path = tmp_path / "not-an-image.txt"
    invalid_path.write_text("not image bytes", encoding="utf-8")

    with pytest.raises(ValueError):
        load_rgb_image(invalid_path)
