import csv

import pytest

from morphoquant.csv_export import MEASUREMENT_COLUMNS, write_measurements_csv


def sample_row():
    return {
        "label": 1,
        "area_px2": 20,
        "area_um2": 5.0,
        "perimeter_px": 18.0,
        "perimeter_um": 4.5,
        "equivalent_diameter_um": 2.52,
        "centroid_x_um": 2.0,
        "centroid_y_um": 3.0,
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
