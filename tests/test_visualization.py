import numpy as np
import pytest
from PIL import Image

from morphoquant.visualization import save_label_overlay


def test_save_label_overlay_creates_preview_and_preserves_source(tmp_path):
    image = np.full((20, 30, 3), 120, dtype=np.uint8)
    original = image.copy()
    labels = np.zeros((20, 30), dtype=np.uint8)
    labels[3:12, 4:16] = 1
    labels[13:18, 20:27] = 2
    output = tmp_path / "nested" / "overlay.png"

    written = save_label_overlay(
        image, labels, output,
        class_names={1: "cortex", 2: "medulla"},
        alpha=0.4,
    )

    assert written == output.resolve()
    assert output.is_file()
    rendered = np.asarray(Image.open(output).convert("RGB"))
    assert rendered.shape[0] > image.shape[0]
    assert rendered.shape[1] > image.shape[1] * 2
    assert np.any(rendered != 120)
    assert np.array_equal(image, original)


def test_save_label_overlay_background_only_mask_creates_preview(tmp_path):
    image = np.full((8, 9, 3), 200, dtype=np.uint8)
    labels = np.zeros((8, 9), dtype=np.uint8)
    output = tmp_path / "empty.png"
    save_label_overlay(image, labels, output)
    assert output.is_file()


@pytest.mark.parametrize(
    "image,labels",
    [
        (np.zeros((5, 5), dtype=np.uint8), np.zeros((5, 5), dtype=np.uint8)),
        (np.zeros((5, 5, 3), dtype=float), np.zeros((5, 5), dtype=np.uint8)),
        (np.zeros((5, 5, 3), dtype=np.uint8), np.zeros((4, 5), dtype=np.uint8)),
        (np.zeros((5, 5, 3), dtype=np.uint8), np.zeros((5, 5), dtype=float)),
        (np.zeros((5, 5, 3), dtype=np.uint8), -np.ones((5, 5), dtype=int)),
    ],
)
def test_save_label_overlay_rejects_invalid_images_and_masks(tmp_path, image, labels):
    with pytest.raises((TypeError, ValueError)):
        save_label_overlay(image, labels, tmp_path / "invalid.png")


@pytest.mark.parametrize("alpha", [-0.1, 1.1, float("nan"), True])
def test_save_label_overlay_rejects_invalid_alpha(tmp_path, alpha):
    with pytest.raises((TypeError, ValueError)):
        save_label_overlay(
            np.zeros((5, 5, 3), dtype=np.uint8),
            np.zeros((5, 5), dtype=np.uint8),
            tmp_path / "invalid.png",
            alpha=alpha,
        )


def test_save_label_overlay_requires_png_extension(tmp_path):
    with pytest.raises(ValueError, match="png extension"):
        save_label_overlay(
            np.zeros((5, 5, 3), dtype=np.uint8),
            np.zeros((5, 5), dtype=np.uint8),
            tmp_path / "overlay.jpg",
        )


def test_save_label_overlay_downscales_large_preview(tmp_path):
    image = np.full((100, 200, 3), 100, dtype=np.uint8)
    labels = np.zeros((100, 200), dtype=np.uint8)
    labels[20:80, 40:160] = 1
    output = tmp_path / "scaled.png"
    save_label_overlay(image, labels, output, max_dimension=50)
    rendered = Image.open(output)
    assert rendered.width <= 2 * 50 + 20 * 3 + 20
    assert rendered.height > 50
