import math

import numpy as np
import pytest

from morphoquant import MicroscopeCalibration, measure_binary_mask


def test_calibration_converts_length_and_area():
    calibration = MicroscopeCalibration(micrometers_per_pixel=0.5)
    assert calibration.length_um(10) == pytest.approx(5.0)
    assert calibration.area_um2(100) == pytest.approx(25.0)


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_calibration_rejects_invalid_scale(value):
    with pytest.raises(ValueError):
        MicroscopeCalibration(micrometers_per_pixel=value)


def test_measure_binary_mask_returns_expected_area_and_centroid():
    mask = np.zeros((30, 30), dtype=bool)
    mask[5:15, 8:28] = True  # 10 x 20 pixels; synthetic test region only.
    calibration = MicroscopeCalibration(micrometers_per_pixel=0.5)

    results = measure_binary_mask(mask, calibration)

    assert len(results) == 1
    measured = results[0]
    assert measured["area_px2"] == 200
    assert measured["area_um2"] == pytest.approx(50.0)
    assert measured["centroid_x_um"] == pytest.approx(8.75 * 0.5)
    assert measured["centroid_y_um"] == pytest.approx(9.5 * 0.5)
    assert measured["equivalent_diameter_um"] == pytest.approx(
        math.sqrt(4 * 50.0 / math.pi)
    )


def test_minimum_area_filter_excludes_small_components():
    mask = np.zeros((20, 20), dtype=bool)
    mask[1:3, 1:3] = True
    mask[8:18, 8:18] = True
    calibration = MicroscopeCalibration(micrometers_per_pixel=1.0)

    results = measure_binary_mask(mask, calibration, min_area_px=10)

    assert len(results) == 1
    assert results[0]["area_px2"] == 100


def test_mask_must_be_boolean_and_two_dimensional():
    calibration = MicroscopeCalibration(micrometers_per_pixel=1.0)
    with pytest.raises(TypeError):
        measure_binary_mask(np.zeros((5, 5), dtype=np.uint8), calibration)
    with pytest.raises(ValueError):
        measure_binary_mask(np.zeros((2, 5, 5), dtype=bool), calibration)
