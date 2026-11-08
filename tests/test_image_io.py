import numpy as np
import pytest
from PIL import Image

from morphoquant.image_io import load_rgb_image, load_labeled_volume_tiff


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


def test_load_labeled_volume_tiff_reads_ome_zyx_integer_stack(tmp_path):
    import tifffile

    labels = np.zeros((4, 8, 9), dtype=np.uint16)
    labels[1:3, 2:6, 3:7] = 2
    path = tmp_path / "labels.ome.tif"
    tifffile.imwrite(
        path,
        labels,
        ome=True,
        metadata={
            "axes": "ZYX",
            "PhysicalSizeX": 0.25,
            "PhysicalSizeXUnit": "µm",
            "PhysicalSizeY": 0.25,
            "PhysicalSizeYUnit": "µm",
            "PhysicalSizeZ": 1.0,
            "PhysicalSizeZUnit": "µm",
        },
    )
    actual = load_labeled_volume_tiff(path)
    assert actual.shape == labels.shape
    assert actual.dtype == labels.dtype
    assert np.array_equal(actual, labels)


def test_load_labeled_volume_tiff_enforces_memory_limit(tmp_path):
    import tifffile

    labels = np.zeros((4, 8, 9), dtype=np.uint16)
    path = tmp_path / "labels.ome.tif"
    tifffile.imwrite(path, labels, ome=True, metadata={"axes": "ZYX"})
    with pytest.raises(ValueError, match="exceeding the configured limit"):
        load_labeled_volume_tiff(path, max_uncompressed_bytes=10)


def test_load_labeled_volume_tiff_rejects_non_zyx_axes(tmp_path):
    import tifffile

    labels = np.zeros((4, 8, 9, 3), dtype=np.uint8)
    path = tmp_path / "channels.ome.tif"
    tifffile.imwrite(path, labels, ome=True, metadata={"axes": "ZYXC"})
    with pytest.raises(ValueError, match="axes='ZYX'"):
        load_labeled_volume_tiff(path)
