import numpy as np
import pytest
import tifffile

from morphoquant.tiff_metadata import read_tiff_metadata


def test_read_ome_tiff_metadata_extracts_physical_pixel_sizes(tmp_path):
    path = tmp_path / "calibrated.ome.tif"
    image = np.zeros((12, 18), dtype=np.uint16)
    tifffile.imwrite(
        path,
        image,
        ome=True,
        metadata={
            "axes": "YX",
            "PhysicalSizeX": 0.25,
            "PhysicalSizeXUnit": "µm",
            "PhysicalSizeY": 0.30,
            "PhysicalSizeYUnit": "µm",
        },
    )

    metadata = read_tiff_metadata(path)

    assert metadata.is_ome_tiff is True
    assert metadata.axes == "YX"
    assert metadata.shape == (12, 18)
    assert metadata.dtype == "uint16"
    assert metadata.pixel_size_x_um == pytest.approx(0.25)
    assert metadata.pixel_size_y_um == pytest.approx(0.30)
    assert metadata.has_physical_calibration is True
    assert metadata.is_isotropic is False
    calibration = metadata.to_calibration()
    assert calibration.scale_x_um == pytest.approx(0.25)
    assert calibration.scale_y_um == pytest.approx(0.30)


def test_plain_tiff_without_resolution_does_not_invent_calibration(tmp_path):
    path = tmp_path / "uncalibrated.tif"
    tifffile.imwrite(path, np.zeros((10, 10), dtype=np.uint8))

    metadata = read_tiff_metadata(path)

    assert metadata.has_physical_calibration is False
    assert metadata.pixel_size_x_um is None
    assert metadata.pixel_size_y_um is None
    with pytest.raises(ValueError, match="does not contain valid physical pixel sizes"):
        metadata.to_calibration()


def test_read_tiff_metadata_rejects_missing_or_invalid_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_tiff_metadata(tmp_path / "missing.tif")

    bad = tmp_path / "bad.tif"
    bad.write_text("not a tiff", encoding="utf-8")
    with pytest.raises(ValueError, match="Could not read TIFF metadata"):
        read_tiff_metadata(bad)
