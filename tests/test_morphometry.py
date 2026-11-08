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
    assert measured["centroid_x_um"] == pytest.approx(17.5 * 0.5)
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


def test_anisotropic_calibration_uses_both_pixel_axes():
    calibration = MicroscopeCalibration(
        micrometers_per_pixel_x=0.5,
        micrometers_per_pixel_y=1.0,
    )
    assert calibration.scale_x_um == pytest.approx(0.5)
    assert calibration.scale_y_um == pytest.approx(1.0)
    assert calibration.area_um2(200) == pytest.approx(100.0)
    assert calibration.is_isotropic is False


def test_anisotropic_measurements_scale_area_centroid_and_perimeter():
    mask = np.zeros((30, 30), dtype=bool)
    mask[5:15, 8:28] = True
    calibration = MicroscopeCalibration(
        micrometers_per_pixel_x=0.5,
        micrometers_per_pixel_y=1.0,
    )

    result = measure_binary_mask(mask, calibration)[0]

    assert result["area_px2"] == 200
    assert result["area_um2"] == pytest.approx(100.0)
    assert result["centroid_x_um"] == pytest.approx(8.75)
    assert result["centroid_y_um"] == pytest.approx(9.5)
    assert result["perimeter_um"] == pytest.approx(40.0, abs=1.0)
    assert result["pixel_size_x_um"] == pytest.approx(0.5)
    assert result["pixel_size_y_um"] == pytest.approx(1.0)


def test_calibration_rejects_incomplete_or_mixed_axis_scales():
    with pytest.raises(ValueError):
        MicroscopeCalibration(micrometers_per_pixel_x=0.5)
    with pytest.raises(ValueError):
        MicroscopeCalibration(
            micrometers_per_pixel=0.5,
            micrometers_per_pixel_x=0.5,
            micrometers_per_pixel_y=0.5,
        )


def test_calibration_can_be_derived_from_measured_scale_bar():
    calibration = MicroscopeCalibration.from_isotropic_reference(
        reference_pixels=200,
        reference_length_um=50,
    )
    assert calibration.scale_x_um == pytest.approx(0.25)
    assert calibration.scale_y_um == pytest.approx(0.25)


@pytest.mark.parametrize(
    "pixels,length",
    [(0, 50), (-1, 50), (200, 0), (200, float("nan"))],
)
def test_scale_bar_calibration_rejects_invalid_reference(pixels, length):
    with pytest.raises(ValueError):
        MicroscopeCalibration.from_isotropic_reference(
            reference_pixels=pixels,
            reference_length_um=length,
        )
