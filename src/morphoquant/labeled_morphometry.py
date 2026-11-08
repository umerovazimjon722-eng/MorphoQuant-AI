"""Morphometry for multi-class, researcher-annotated 2D label masks."""

from numbers import Integral
from typing import Dict, List, Mapping

import numpy as np
from skimage.measure import label, regionprops

from .calibration import MicroscopeCalibration
from .morphometry import _contour_perimeter


def measure_labeled_mask(
    mask: np.ndarray,
    calibration: MicroscopeCalibration,
    *,
    background_label: int = 0,
    label_names: Mapping[int, str] | None = None,
    min_component_area_px: int = 1,
) -> List[Dict[str, float | int | str]]:
    """Summarize measurements separately for each annotation class.

    This function does not segment tissue. The input integer label image must
    be annotated and reviewed by a researcher before it is analyzed.
    """
    if not isinstance(calibration, MicroscopeCalibration):
        raise TypeError("calibration must be a MicroscopeCalibration instance.")
    if isinstance(background_label, bool) or not isinstance(background_label, Integral):
        raise TypeError("background_label must be an integer.")
    if isinstance(min_component_area_px, bool) or not isinstance(min_component_area_px, Integral):
        raise TypeError("min_component_area_px must be an integer.")
    if min_component_area_px < 1:
        raise ValueError("min_component_area_px must be at least 1.")

    array = np.asarray(mask)
    if array.ndim != 2:
        raise ValueError("mask must be a two-dimensional array.")
    if array.dtype == np.bool_ or not np.issubdtype(array.dtype, np.integer):
        raise TypeError("mask must contain integer class labels, not Boolean or floating values.")
    if np.any(array < 0):
        raise ValueError("mask labels must be non-negative.")
    if label_names is not None:
        if not isinstance(label_names, Mapping):
            raise TypeError("label_names must be a mapping from integer IDs to names.")
        for class_id, name in label_names.items():
            if isinstance(class_id, bool) or not isinstance(class_id, Integral):
                raise TypeError("label_names keys must be integer class IDs.")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("label_names values must be non-empty strings.")

    pixel_size_x = calibration.scale_x_um
    pixel_size_y = calibration.scale_y_um
    class_ids = [
        int(value) for value in np.unique(array) if int(value) != int(background_label)
    ]
    if not class_ids:
        return []

    regions_by_class: Dict[int, list] = {}
    areas_by_class: Dict[int, int] = {}
    for class_id in class_ids:
        connected = label(array == class_id, connectivity=2)
        pixel_regions = regionprops(connected)
        physical_regions = regionprops(
            connected,
            spacing=(pixel_size_y, pixel_size_x),
        )
        retained = [
            (pixel_region, physical_region)
            for pixel_region, physical_region in zip(pixel_regions, physical_regions)
            if int(pixel_region.area) >= int(min_component_area_px)
        ]
        regions_by_class[class_id] = retained
        areas_by_class[class_id] = sum(int(pixel_region.area) for pixel_region, _ in retained)

    total_foreground_px = sum(areas_by_class.values())
    output: List[Dict[str, float | int | str]] = []

    for class_id in class_ids:
        retained = regions_by_class[class_id]
        if not retained:
            continue

        area_px2 = areas_by_class[class_id]
        area_um2 = float(area_px2 * pixel_size_x * pixel_size_y)
        perimeters_px: List[float] = []
        perimeters_um: List[float] = []
        component_areas_um2: List[float] = []
        equivalent_diameters_um: List[float] = []
        eccentricities: List[float] = []
        solidities: List[float] = []
        weighted_x_sum = 0.0
        weighted_y_sum = 0.0

        for pixel_region, physical_region in retained:
            perimeter_px, perimeter_um = _contour_perimeter(
                pixel_region.image,
                pixel_size_y_um=pixel_size_y,
                pixel_size_x_um=pixel_size_x,
            )
            component_area = float(physical_region.area)
            perimeters_px.append(perimeter_px)
            perimeters_um.append(perimeter_um)
            component_areas_um2.append(component_area)
            equivalent_diameters_um.append(float(physical_region.equivalent_diameter_area))
            eccentricities.append(float(physical_region.eccentricity))
            solidities.append(float(physical_region.solidity))
            centroid_y_um, centroid_x_um = physical_region.centroid
            weighted_x_sum += float(centroid_x_um) * component_area
            weighted_y_sum += float(centroid_y_um) * component_area

        class_name = (
            str(label_names[class_id]).strip()
            if label_names is not None and class_id in label_names
            else str(class_id)
        )
        output.append(
            {
                "class_id": int(class_id),
                "class_name": class_name,
                "component_count": len(retained),
                "area_px2": int(area_px2),
                "area_um2": area_um2,
                "foreground_area_percent": float(100.0 * area_px2 / total_foreground_px),
                "mean_component_area_um2": float(np.mean(component_areas_um2)),
                "median_component_area_um2": float(np.median(component_areas_um2)),
                "mean_equivalent_diameter_um": float(np.mean(equivalent_diameters_um)),
                "total_perimeter_px": float(np.sum(perimeters_px)),
                "total_perimeter_um": float(np.sum(perimeters_um)),
                "area_weighted_centroid_x_um": float(weighted_x_sum / area_um2),
                "area_weighted_centroid_y_um": float(weighted_y_sum / area_um2),
                "mean_component_eccentricity": float(np.mean(eccentricities)),
                "mean_component_solidity": float(np.mean(solidities)),
                "pixel_size_x_um": float(pixel_size_x),
                "pixel_size_y_um": float(pixel_size_y),
            }
        )

    return output
