"""Synthetic demonstration of class-wise adrenal-zone morphometry.

The generated arrays are artificial software-test examples, not histological
observations and not data from animals or patients.
"""

import numpy as np

from morphoquant import MicroscopeCalibration, measure_labeled_mask


def main() -> None:
    # 0 = background, 1 = synthetic cortex label, 2 = synthetic medulla label.
    label_image = np.zeros((120, 160), dtype=np.uint8)
    label_image[10:100, 10:150] = 1
    label_image[35:75, 45:115] = 2

    # Demonstration calibration only. Replace with a measured microscope scale.
    calibration = MicroscopeCalibration(
        micrometers_per_pixel_x=0.25,
        micrometers_per_pixel_y=0.27,
    )
    results = measure_labeled_mask(
        label_image,
        calibration,
        label_names={1: "synthetic_cortex", 2: "synthetic_medulla"},
        min_component_area_px=10,
    )

    for row in results:
        print(row)


if __name__ == "__main__":
    main()
