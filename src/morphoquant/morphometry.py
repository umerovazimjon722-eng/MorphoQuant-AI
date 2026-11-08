"""Basic morphometry for researcher-provided 2D binary masks.

This module does not perform segmentation. It measures connected components
in a Boolean mask supplied by the caller.
"""

from typing import Dict, List

import numpy as np
from skimage.measure import find_contours, label, regionprops

from .calibration import MicroscopeCalibration


def _contour_perimeter(
    component_mask: np.ndarray,
    *,
    pixel_size_y_um: float,
    pixel_size_x_um: float,
) -> tuple[float, float]:
    """Estimate contour length in pixels and micrometres using marching squares."""
    padded = np.pad(component_mask.astype(np.uint8), 1, mode="constant")
    contours = find_contours(padded, level=0.5, fully_connected="high")
    perimeter_px = 0.0
    perimeter_um = 0.0

    for contour in contours:
        steps = np.diff(contour, axis=0)
        dy_px = steps[:, 0]
        dx_px = steps[:, 1]
        perimeter_px += float(np.hypot(dx_px, dy_px).sum())
        perimeter_um += float(
            np.hypot(dx_px * pixel_size_x_um, dy_px * pixel_size_y_um).sum()
        )

    return perimeter_px, perimeter_um


def measure_binary_mask(
    mask: np.ndarray,
    calibration: MicroscopeCalibration,
    min_area_px: int = 1,
) -> List[Dict[str, float]]:
    """Measure connected components in a 2D Boolean mask.

    The image is treated as an 8-connected 2D plane. Physical area, centroids,
    equivalent diameter, and shape descriptors use the supplied x/y pixel
    spacing. Perimeter is estimated from 0.5-level marching-squares contours,
    with each axis scaled separately.

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
        One dictionary per component. Pixel and physical measurements are
        returned together. Perimeter is a digital contour estimate and remains
        dependent on resolution, connectivity, and boundary discretization.
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

    for pixel_region, physical_region in zip(pixel_regions, physical_regions):
        area_px2 = int(pixel_region.area)
        if area_px2 < min_area_px:
            continue

        centroid_y_px, centroid_x_px = pixel_region.centroid
        centroid_y_um, centroid_x_um = physical_region.centroid
        perimeter_px, perimeter_um = _contour_perimeter(
            pixel_region.image,
            pixel_size_y_um=calibration.scale_y_um,
            pixel_size_x_um=calibration.scale_x_um,
        )

        output.append(
            {
                "label": int(pixel_region.label),
                "area_px2": area_px2,
                "area_um2": float(physical_region.area),
                "perimeter_px": perimeter_px,
                "perimeter_um": perimeter_um,
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
