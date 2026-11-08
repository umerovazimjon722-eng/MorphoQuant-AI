"""Basic morphometry for researcher-provided 2D binary masks.

This module does not perform segmentation. It measures connected components
in a Boolean mask supplied by the caller.
"""

from typing import Dict, List

import numpy as np
from skimage.measure import label, regionprops

from .calibration import MicroscopeCalibration


def measure_binary_mask(
    mask: np.ndarray,
    calibration: MicroscopeCalibration,
    min_area_px: int = 1,
) -> List[Dict[str, float]]:
    """Measure connected components in a 2D Boolean mask.

    The image is treated as an 8-connected 2D plane. Physical descriptors are
    calculated with the supplied x/y pixel spacing, so anisotropic images are
    not incorrectly treated as square pixels.

    Parameters
    ----------
    mask:
        Two-dimensional Boolean array; True pixels represent foreground.
    calibration:
        Explicit microscope pixel spacing. Supply either an isotropic scale or
        separate x/y micrometres-per-pixel values.
    min_area_px:
        Minimum component area in pixels. Components below this value are
        omitted.

    Returns
    -------
    list of dict
        One dictionary per component. Pixel area and perimeter are reported
        alongside physical area, perimeter, equivalent diameter, and centroid.
        The perimeter remains a digital boundary estimator and is resolution-
        and discretization-dependent.
    """
    if not isinstance(calibration, MicroscopeCalibration):
        raise TypeError("calibration must be a MicroscopeCalibration instance.")

    array = np.asarray(mask)
    if array.ndim != 2:
        raise ValueError("mask must be a two-dimensional array.")
    if array.dtype != np.bool_:
        raise TypeError("mask must have Boolean dtype; convert a reviewed mask explicitly.")
    if isinstance(min_area_px, bool) or not isinstance(min_area_px, int):
        raise TypeError("min_area_px must be an integer.")
    if min_area_px < 1:
        raise ValueError("min_area_px must be at least 1.")

    labeled = label(array, connectivity=2)
    pixel_regions = regionprops(labeled)
    physical_regions = regionprops(
        labeled,
        spacing=(calibration.scale_y_um, calibration.scale_x_um),
    )

    output: List[Dict[str, float]] = []
    pixel_area_scale = calibration.scale_x_um * calibration.scale_y_um

    for pixel_region, physical_region in zip(pixel_regions, physical_regions):
        area_px2 = int(pixel_region.area)
        if area_px2 < min_area_px:
            continue

        centroid_y_px, centroid_x_px = pixel_region.centroid
        centroid_y_um, centroid_x_um = physical_region.centroid

        output.append(
            {
                "label": int(pixel_region.label),
                "area_px2": area_px2,
                "area_um2": float(physical_region.area),
                "perimeter_px": float(pixel_region.perimeter),
                "perimeter_um": float(physical_region.perimeter),
                "equivalent_diameter_um": float(physical_region.equivalent_diameter_area),
                "centroid_x_px": float(centroid_x_px),
                "centroid_y_px": float(centroid_y_px),
                "centroid_x_um": float(centroid_x_um),
                "centroid_y_um": float(centroid_y_um),
                "pixel_size_x_um": float(calibration.scale_x_um),
                "pixel_size_y_um": float(calibration.scale_y_um),
                "eccentricity": float(physical_region.eccentricity),
                "solidity": float(physical_region.solidity),
            }
        )

    return output
