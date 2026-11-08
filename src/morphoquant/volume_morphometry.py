"""3D morphometry for researcher-annotated integer label volumes."""

from numbers import Integral
from typing import Dict, List, Mapping

import numpy as np
from skimage.measure import label, marching_cubes, mesh_surface_area, regionprops

from .calibration import VoxelCalibration


def _component_surface_area(
    component: np.ndarray,
    spacing_zyx_um: tuple[float, float, float],
) -> float:
    """Estimate a component surface using a padded marching-cubes mesh."""
    padded = np.pad(component.astype(np.uint8), 1, mode="constant")
    vertices, faces, _, _ = marching_cubes(
        padded,
        level=0.5,
        spacing=spacing_zyx_um,
        allow_degenerate=False,
    )
    return float(mesh_surface_area(vertices, faces))


def measure_labeled_volume(
    label_volume: np.ndarray,
    calibration: VoxelCalibration,
    *,
    background_label: int = 0,
    label_names: Mapping[int, str] | None = None,
    min_component_voxels: int = 1,
) -> List[Dict[str, float | int | str]]:
    """Measure 3D class volumes, mesh surface areas, and shape summaries.

    Input is a researcher-annotated integer array in Z-Y-X order. Components
    use 26-connectivity. Physical volume is voxel count multiplied by the
    calibrated Z*Y*X voxel volume. Surface area is estimated from a closed
    marching-cubes mesh on a one-voxel padded component.

    The volume must already be aligned and annotated. This function does not
    register serial sections, resample or interpolate missing planes, segment
    tissue, or infer biological labels. A 3D volume fraction is meaningful
    only when acquisition and section sampling form a valid 3D reconstruction.
    """
    if not isinstance(calibration, VoxelCalibration):
        raise TypeError("calibration must be a VoxelCalibration instance.")
    if isinstance(background_label, bool) or not isinstance(background_label, Integral):
        raise TypeError("background_label must be an integer.")
    if isinstance(min_component_voxels, bool) or not isinstance(min_component_voxels, Integral):
        raise TypeError("min_component_voxels must be an integer.")
    if min_component_voxels < 1:
        raise ValueError("min_component_voxels must be at least 1.")

    volume = np.asarray(label_volume)
    if volume.ndim != 3:
        raise ValueError("label_volume must be a 3D Z-Y-X array.")
    if volume.dtype == np.bool_ or not np.issubdtype(volume.dtype, np.integer):
        raise TypeError("label_volume must contain integer class IDs.")
    if np.any(volume < 0):
        raise ValueError("label_volume class IDs must be non-negative.")
    if label_names is not None:
        if not isinstance(label_names, Mapping):
            raise TypeError("label_names must map integer class IDs to names.")
        for class_id, name in label_names.items():
            if isinstance(class_id, bool) or not isinstance(class_id, Integral):
                raise TypeError("label_names keys must be integer class IDs.")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("label_names values must be non-empty strings.")

    class_ids = {
        int(value) for value in np.unique(volume)
        if int(value) != int(background_label)
    }
    if label_names is not None:
        class_ids.update(
            int(value) for value in label_names
            if int(value) != int(background_label)
        )
    voxel_volume = calibration.voxel_volume_um3
    spacing = calibration.spacing_zyx_um

    retained_by_class = {}
    volume_by_class = {}
    for class_id in sorted(class_ids):
        connected = label(volume == class_id, connectivity=3)
        regions = regionprops(connected, spacing=spacing)
        retained = [
            region for region in regions
            if int(round(float(region.area) / voxel_volume)) >= int(min_component_voxels)
        ]
        retained_by_class[class_id] = retained
        volume_by_class[class_id] = float(sum(float(region.area) for region in retained))

    total_volume = float(sum(volume_by_class.values()))
    results: List[Dict[str, float | int | str]] = []

    for class_id in sorted(class_ids):
        regions = retained_by_class[class_id]
        if not regions:
            continue

        component_volumes = [float(region.area) for region in regions]
        component_surfaces = [
            _component_surface_area(region.image, spacing)
            for region in regions
        ]
        class_volume = volume_by_class[class_id]
        class_surface = float(sum(component_surfaces))
        sphericity = (
            float(np.pi ** (1.0 / 3.0) * (6.0 * class_volume) ** (2.0 / 3.0) / class_surface)
            if class_surface > 0
            else None
        )
        centroids = np.asarray([region.centroid for region in regions], dtype=float)
        weighted_centroid = np.average(
            centroids,
            axis=0,
            weights=np.asarray(component_volumes, dtype=float),
        )
        class_name = (
            str(label_names[class_id]).strip()
            if label_names is not None and class_id in label_names
            else str(class_id)
        )
        results.append(
            {
                "class_id": int(class_id),
                "class_name": class_name,
                "component_count": len(regions),
                "voxel_count": int(round(class_volume / voxel_volume)),
                "volume_um3": class_volume,
                "foreground_volume_percent": (
                    float(100.0 * class_volume / total_volume) if total_volume else 0.0
                ),
                "mean_component_volume_um3": float(np.mean(component_volumes)),
                "median_component_volume_um3": float(np.median(component_volumes)),
                "mean_equivalent_sphere_diameter_um": float(np.mean([
                    2.0 * (3.0 * float(region.area) / (4.0 * np.pi)) ** (1.0 / 3.0)
                    for region in regions
                ])),
                "total_surface_area_um2": class_surface,
                "sphericity": sphericity,
                "volume_weighted_centroid_z_um": float(weighted_centroid[0]),
                "volume_weighted_centroid_y_um": float(weighted_centroid[1]),
                "volume_weighted_centroid_x_um": float(weighted_centroid[2]),
                "voxel_size_z_um": float(spacing[0]),
                "voxel_size_y_um": float(spacing[1]),
                "voxel_size_x_um": float(spacing[2]),
                "connectivity": 26,
            }
        )
    return results
