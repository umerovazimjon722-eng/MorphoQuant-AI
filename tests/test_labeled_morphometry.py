import numpy as np
import pytest

from morphoquant import MicroscopeCalibration, measure_labeled_mask


def test_measure_labeled_mask_summarizes_cortex_and_medulla():
    mask = np.zeros((30, 40), dtype=np.uint8)
    mask[2:12, 2:22] = 1
    mask[16:26, 24:34] = 2
    calibration = MicroscopeCalibration(
        micrometers_per_pixel_x=0.5,
        micrometers_per_pixel_y=1.0,
    )

    results = measure_labeled_mask(
        mask,
        calibration,
        label_names={1: "cortex", 2: "medulla"},
    )

    assert len(results) == 2
    cortex, medulla = results
    assert cortex["class_name"] == "cortex"
    assert medulla["class_name"] == "medulla"
    assert cortex["area_px2"] == 200
    assert medulla["area_px2"] == 100
    assert cortex["area_um2"] == pytest.approx(100.0)
    assert medulla["area_um2"] == pytest.approx(50.0)
    assert cortex["foreground_area_percent"] == pytest.approx(200 / 300 * 100)
    assert medulla["foreground_area_percent"] == pytest.approx(100 / 300 * 100)
    assert cortex["component_count"] == 1
    assert medulla["component_count"] == 1


def test_measure_labeled_mask_counts_disconnected_components_by_class():
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[1:4, 1:4] = 1
    mask[10:15, 10:15] = 1
    mask[5:8, 5:8] = 2

    results = measure_labeled_mask(
        mask,
        MicroscopeCalibration(micrometers_per_pixel=1.0),
    )

    by_id = {row["class_id"]: row for row in results}
    assert by_id[1]["component_count"] == 2
    assert by_id[1]["area_px2"] == 34
    assert by_id[2]["component_count"] == 1
    assert by_id[2]["foreground_area_percent"] == pytest.approx(9 / 43 * 100)


def test_measure_labeled_mask_excludes_background_and_small_components():
    mask = np.zeros((12, 12), dtype=np.uint8)
    mask[1:3, 1:3] = 1
    mask[5:10, 5:10] = 2

    results = measure_labeled_mask(
        mask,
        MicroscopeCalibration(micrometers_per_pixel=1.0),
        min_component_area_px=5,
    )

    assert [row["class_id"] for row in results] == [2]
    assert results[0]["area_px2"] == 25


def test_measure_labeled_mask_handles_background_only_image():
    mask = np.zeros((8, 8), dtype=np.uint16)
    results = measure_labeled_mask(mask, MicroscopeCalibration(1.0))
    assert results == []


@pytest.mark.parametrize(
    "mask",
    [
        np.zeros((5, 5), dtype=float),
        np.zeros((5, 5), dtype=bool),
        -np.ones((5, 5), dtype=int),
        np.zeros((2, 5, 5), dtype=int),
    ],
)
def test_measure_labeled_mask_rejects_invalid_arrays(mask):
    with pytest.raises((TypeError, ValueError)):
        measure_labeled_mask(mask, MicroscopeCalibration(1.0))


def test_measure_labeled_mask_validates_label_names():
    mask = np.zeros((5, 5), dtype=np.uint8)
    mask[1:3, 1:3] = 1
    with pytest.raises(ValueError):
        measure_labeled_mask(
            mask,
            MicroscopeCalibration(1.0),
            label_names={1: ""},
        )
