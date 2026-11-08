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
    """Measure connected components in a two-dimensional Boolean mask.

    Parameters
    ----------
    mask:
        2D Boolean array. True pixels are foreground regions.
    calibration:
        Explicit isotropic microscope calibration in micrometres per pixel.
    min_area_px:
        Minimum component area in pixels. Components smaller than this value
        are omitted. The default retains every non-empty component.

    Returns
    -------
    list of dict
        One dictionary per retained connected component. Coordinates use
        zero-based image coordinates, with x corresponding to columns and
        y corresponding to rows. Lengths are in micrometres and areas are in
        square micrometres.
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
    output: List[Dict[str, float]] = []

    for region in regionprops(labeled):
        if region.area < min_area_px:
            continue

        # region.perimeter is an estimator in pixel units; its value can vary
        # with resolution and boundary discretization. Use consistently.
        centroid_y_px, centroid_x_px = region.centroid
        scale = calibration.micrometers_per_pixel

        output.append(
            {
                "label": int(region.label),
                "area_px2": int(region.area),
                "area_um2": calibration.area_um2(float(region.area)),
                "perimeter_px": float(region.perimeter),
                "perimeter_um": calibration.length_um(float(region.perimeter)),
                "equivalent_diameter_um": calibration.length_um(
                    float(region.equivalent_diameter_area)
                ),
                "centroid_x_um": float(centroid_x_px * scale),
                "centroid_y_um": float(centroid_y_px * scale),
                "eccentricity": float(region.eccentricity),
                "solidity": float(region.solidity),
            }
        )

    return output
