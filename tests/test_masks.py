import numpy as np
import pytest
from PIL import Image

from morphoquant.masks import load_binary_mask


def test_load_binary_mask_accepts_two_level_mask(tmp_path):
    source = np.zeros((8, 9), dtype=np.uint8)
    source[2:5, 3:7] = 255
    path = tmp_path / "mask.png"
    Image.fromarray(source, mode="L").save(path)

    result = load_binary_mask(path)

    assert result.dtype == np.bool_
    assert result.shape == source.shape
    assert int(result.sum()) == 12


def test_load_binary_mask_supports_dark_foreground(tmp_path):
    source = np.full((5, 5), 255, dtype=np.uint8)
    source[1:4, 1:4] = 0
    path = tmp_path / "dark-mask.png"
    Image.fromarray(source, mode="L").save(path)

    result = load_binary_mask(path, foreground="dark")

    assert int(result.sum()) == 9


def test_load_binary_mask_requires_threshold_for_grayscale_image(tmp_path):
    source = np.arange(25, dtype=np.uint8).reshape(5, 5)
    path = tmp_path / "grayscale.png"
    Image.fromarray(source, mode="L").save(path)

    with pytest.raises(ValueError, match="explicit threshold"):
        load_binary_mask(path)

    result = load_binary_mask(path, threshold=12)
    assert int(result.sum()) == 12


def test_load_binary_mask_rejects_rgb_images(tmp_path):
    path = tmp_path / "rgb.png"
    Image.fromarray(np.zeros((5, 5, 3), dtype=np.uint8), mode="RGB").save(path)

    with pytest.raises(ValueError, match="grayscale"):
        load_binary_mask(path)


def test_load_binary_mask_constant_image_is_empty(tmp_path):
    path = tmp_path / "empty.png"
    Image.fromarray(np.zeros((5, 5), dtype=np.uint8), mode="L").save(path)

    result = load_binary_mask(path)

    assert not result.any()
