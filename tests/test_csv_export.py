import csv

import pytest

from morphoquant.csv_export import (
    LABELED_MEASUREMENT_COLUMNS,
    MEASUREMENT_COLUMNS,
    write_labeled_measurements_csv,
    write_measurements_csv,
)


def sample_row():
    return {
        "label": 1,
        "area_px2": 20,
        "area_um2": 5.0,
        "perimeter_px": 18.0,
        "perimeter_um": 4.5,
        "equivalent_diameter_um": 2.52,
        "centroid_x_px": 4.0,
        "centroid_y_px": 6.0,
        "centroid_x_um": 2.0,
        "centroid_y_um": 3.0,
        "pixel_size_x_um": 0.5,
        "pixel_size_y_um": 0.5,
        "eccentricity": 0.5,
        "solidity": 1.0,
    }


def test_write_measurements_csv_writes_header_and_data(tmp_path):
    output = tmp_path / "nested" / "measurements.csv"

    written = write_measurements_csv([sample_row()], output)

    assert written == output
    with output.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert list(rows[0]) == list(MEASUREMENT_COLUMNS)
    assert rows[0]["label"] == "1"
    assert rows[0]["area_um2"] == "5.0"


def test_write_measurements_csv_writes_header_for_empty_results(tmp_path):
    output = tmp_path / "empty.csv"
    write_measurements_csv([], output)

    with output.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file)
        assert next(reader) == list(MEASUREMENT_COLUMNS)
        assert list(reader) == []


def test_write_measurements_csv_rejects_incomplete_row(tmp_path):
    with pytest.raises(ValueError, match="missing required fields"):
        write_measurements_csv([{"label": 1}], tmp_path / "bad.csv")


def test_write_labeled_measurements_csv_preserves_class_summary_schema(tmp_path):
    row = {
        "class_id": 1,
        "class_name": "cortex",
        "component_count": 2,
        "area_px2": 100,
        "area_um2": 25.0,
        "foreground_area_percent": 75.0,
        "mean_component_area_um2": 12.5,
        "median_component_area_um2": 12.5,
        "mean_equivalent_diameter_um": 3.0,
        "total_perimeter_px": 40.0,
        "total_perimeter_um": 10.0,
        "area_weighted_centroid_x_um": 2.0,
        "area_weighted_centroid_y_um": 3.0,
        "mean_component_eccentricity": 0.3,
        "mean_component_solidity": 0.9,
        "pixel_size_x_um": 0.5,
        "pixel_size_y_um": 0.5,
    }
    output = write_labeled_measurements_csv([row], tmp_path / "zones.csv")
    with output.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert list(rows[0]) == list(LABELED_MEASUREMENT_COLUMNS)
    assert rows[0]["class_name"] == "cortex"
    assert rows[0]["foreground_area_percent"] == "75.0"


def test_write_labeled_measurements_csv_rejects_missing_class_fields(tmp_path):
    with pytest.raises(ValueError, match="missing required fields"):
        write_labeled_measurements_csv([{"class_id": 1}], tmp_path / "bad-zones.csv")


def test_write_volume_measurements_csv_uses_physical_units(tmp_path):
    from morphoquant.csv_export import (
        VOLUME_MEASUREMENT_COLUMNS,
        write_volume_measurements_csv,
    )

    row = {
        "class_id": 1,
        "class_name": "cortex",
        "component_count": 2,
        "voxel_count": 100,
        "volume_um3": 50.0,
        "foreground_volume_percent": 75.0,
        "mean_component_volume_um3": 25.0,
        "median_component_volume_um3": 25.0,
        "mean_equivalent_sphere_diameter_um": 3.0,
        "total_surface_area_um2": 70.0,
        "sphericity": 0.8,
        "volume_weighted_centroid_z_um": 1.0,
        "volume_weighted_centroid_y_um": 2.0,
        "volume_weighted_centroid_x_um": 3.0,
        "voxel_size_z_um": 1.0,
        "voxel_size_y_um": 0.5,
        "voxel_size_x_um": 0.25,
        "connectivity": 26,
    }
    output = write_volume_measurements_csv([row], tmp_path / "volume.csv")
    with output.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    assert list(rows[0]) == list(VOLUME_MEASUREMENT_COLUMNS)
    assert rows[0]["volume_um3"] == "50.0"
    assert rows[0]["connectivity"] == "26"


def test_write_volume_measurements_csv_rejects_incomplete_rows(tmp_path):
    from morphoquant.csv_export import write_volume_measurements_csv

    with pytest.raises(ValueError, match="missing required fields"):
        write_volume_measurements_csv([{"class_id": 1}], tmp_path / "bad.csv")
