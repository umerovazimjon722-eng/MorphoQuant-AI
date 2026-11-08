"""Synthetic 3D adrenal-zone label-volume demonstration.

All arrays in this example are artificial. They do not represent animal,
patient, or experimental histology data.
"""

import numpy as np

from morphoquant import VoxelCalibration, measure_labeled_volume


def main() -> None:
    z_size, y_size, x_size = 40, 100, 100
    z, y, x = np.ogrid[:z_size, :y_size, :x_size]

    center_z, center_y, center_x = 19.5, 49.5, 49.5
    outer = (
        ((z - center_z) / 16.0) ** 2
        + ((y - center_y) / 42.0) ** 2
        + ((x - center_x) / 42.0) ** 2
    ) <= 1.0
    inner = (
        ((z - center_z) / 9.0) ** 2
        + ((y - center_y) / 22.0) ** 2
        + ((x - center_x) / 22.0) ** 2
    ) <= 1.0

    label_volume = np.zeros((z_size, y_size, x_size), dtype=np.uint8)
    label_volume[outer] = 1
    label_volume[inner] = 2

    # Demonstration values only; replace them with verified OME-TIFF metadata.
    calibration = VoxelCalibration(
        micrometers_per_voxel_z=2.0,
        micrometers_per_voxel_y=0.25,
        micrometers_per_voxel_x=0.25,
    )
    results = measure_labeled_volume(
        label_volume,
        calibration,
        label_names={1: "synthetic_cortex", 2: "synthetic_medulla"},
        min_component_voxels=10,
    )

    for result in results:
        print(result)


if __name__ == "__main__":
    main()
