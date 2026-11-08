import json

import numpy as np
from PIL import Image

from morphoquant.calibration import MicroscopeCalibration
from morphoquant.csv_export import write_measurements_csv
from morphoquant.provenance import write_analysis_metadata


def test_write_analysis_metadata_records_inputs_parameters_and_checksums(tmp_path):
    mask_path = tmp_path / "mask.png"
    Image.fromarray(np.zeros((8, 9), dtype=np.uint8), mode="L").save(mask_path)
    csv_path = write_measurements_csv([], tmp_path / "out" / "measurements.csv")
    calibration = MicroscopeCalibration(
        micrometers_per_pixel_x=0.25,
        micrometers_per_pixel_y=0.30,
    )

    metadata_path = write_analysis_metadata(
        input_mask_path=mask_path,
        output_csv_path=csv_path,
        calibration=calibration,
        mask_shape=(8, 9),
        foreground="bright",
        threshold=None,
        min_area_px=3,
        measurement_count=0,
    )

    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert data["segmentation_performed"] is False
    assert data["input_mask"]["file_name"] == "mask.png"
    assert len(data["input_mask"]["sha256"]) == 64
    assert len(data["results"]["csv_sha256"]) == 64
    assert data["calibration"]["pixel_size_x_um"] == 0.25
    assert data["calibration"]["pixel_size_y_um"] == 0.30
    assert data["measurement_parameters"]["minimum_component_area_px"] == 3
    assert data["results"]["component_count"] == 0


def test_write_analysis_metadata_supports_3d_voxel_calibration(tmp_path):
    import json
    import numpy as np
    from PIL import Image
    from morphoquant.calibration import VoxelCalibration
    from morphoquant.csv_export import write_volume_measurements_csv

    source = tmp_path / "labels.tif"
    Image.fromarray(np.zeros((8, 8), dtype=np.uint8), mode="L").save(source)
    row = {
        "class_id": 1, "class_name": "cortex", "component_count": 1,
        "voxel_count": 10, "volume_um3": 2.0, "foreground_volume_percent": 100.0,
        "mean_component_volume_um3": 2.0, "median_component_volume_um3": 2.0,
        "mean_equivalent_sphere_diameter_um": 1.56, "total_surface_area_um2": 5.0,
        "sphericity": 0.8, "volume_weighted_centroid_z_um": 1.0,
        "volume_weighted_centroid_y_um": 2.0, "volume_weighted_centroid_x_um": 3.0,
        "voxel_size_z_um": 1.0, "voxel_size_y_um": 0.5,
        "voxel_size_x_um": 0.4, "connectivity": 26,
    }
    output = write_volume_measurements_csv([row], tmp_path / "volume.csv")
    destination = write_analysis_metadata(
        input_mask_path=source,
        output_csv_path=output,
        calibration=VoxelCalibration(1.0, 0.5, 0.4),
        mask_shape=(3, 8, 8),
        foreground=None,
        threshold=None,
        min_area_px=1,
        measurement_count=1,
        result_count_label="class_count",
        analysis_type="3D test volume",
    )
    data = json.loads(destination.read_text(encoding="utf-8"))
    assert data["input_mask"]["shape_axes_order"] == "ZYX"
    assert data["input_mask"]["shape"] == [3, 8, 8]
    assert data["calibration"]["dimension"] == "3D"
    assert data["calibration"]["voxel_volume_um3"] == 0.2
    assert data["measurement_parameters"]["connectivity"] == 26
