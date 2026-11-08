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
