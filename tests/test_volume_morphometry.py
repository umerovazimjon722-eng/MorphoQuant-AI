import numpy as np
import pytest

from morphoquant import VoxelCalibration, measure_labeled_volume


def test_voxel_calibration_and_anisotropic_volume_measurement():
    calibration = VoxelCalibration(
        micrometers_per_voxel_z=2.0,
        micrometers_per_voxel_y=1.0,
        micrometers_per_voxel_x=0.5,
    )
    assert calibration.spacing_zyx_um == (2.0, 1.0, 0.5)
    assert calibration.voxel_volume_um3 == pytest.approx(1.0)

    labels = np.zeros((10, 12, 14), dtype=np.uint8)
    labels[2:4, 3:7, 4:10] = 1
    result = measure_labeled_volume(
        labels, calibration, label_names={1: "cortex"}
    )[0]
    assert result["class_name"] == "cortex"
    assert result["voxel_count"] == 48
    assert result["volume_um3"] == pytest.approx(48.0)
    assert result["component_count"] == 1
    assert result["total_surface_area_um2"] > 0
    assert result["sphericity"] > 0
    assert result["connectivity"] == 26


def test_volume_morphometry_counts_disconnected_components():
    labels = np.zeros((12, 12, 12), dtype=np.uint8)
    labels[1:3, 1:3, 1:3] = 1
    labels[8:10, 8:10, 8:10] = 1
    result = measure_labeled_volume(
        labels, VoxelCalibration(1.0, 1.0, 1.0)
    )[0]
    assert result["component_count"] == 2
    assert result["voxel_count"] == 16
    assert result["volume_um3"] == pytest.approx(16.0)


def test_volume_morphometry_calculates_class_volume_fractions():
    labels = np.zeros((8, 8, 8), dtype=np.uint8)
    labels[1:4, 1:4, 1:4] = 1
    labels[4:6, 4:6, 4:6] = 2
    results = measure_labeled_volume(
        labels, VoxelCalibration(1.0, 1.0, 1.0)
    )
    by_id = {row["class_id"]: row for row in results}
    assert by_id[1]["volume_um3"] == pytest.approx(27.0)
    assert by_id[2]["volume_um3"] == pytest.approx(8.0)
    assert by_id[1]["foreground_volume_percent"] == pytest.approx(27 / 35 * 100)


def test_volume_morphometry_applies_minimum_component_voxel_filter():
    labels = np.zeros((10, 10, 10), dtype=np.uint8)
    labels[1:2, 1:2, 1:2] = 1
    labels[4:7, 4:7, 4:7] = 1
    results = measure_labeled_volume(
        labels,
        VoxelCalibration(1.0, 1.0, 1.0),
        min_component_voxels=3,
    )
    assert len(results) == 1
    assert results[0]["voxel_count"] == 27


def test_volume_morphometry_returns_empty_for_background_only():
    labels = np.zeros((4, 5, 6), dtype=np.uint16)
    assert measure_labeled_volume(
        labels, VoxelCalibration(1.0, 1.0, 1.0)
    ) == []


@pytest.mark.parametrize(
    "labels",
    [
        np.zeros((4, 4), dtype=np.uint8),
        np.zeros((3, 4, 4), dtype=float),
        np.zeros((3, 4, 4), dtype=bool),
        -np.ones((3, 4, 4), dtype=int),
    ],
)
def test_volume_morphometry_rejects_invalid_arrays(labels):
    with pytest.raises((TypeError, ValueError)):
        measure_labeled_volume(labels, VoxelCalibration(1.0, 1.0, 1.0))


def test_volume_morphometry_rejects_invalid_class_names():
    labels = np.zeros((3, 3, 3), dtype=np.uint8)
    labels[1, 1, 1] = 1
    with pytest.raises(ValueError):
        measure_labeled_volume(
            labels, VoxelCalibration(1.0, 1.0, 1.0), label_names={1: ""}
        )
