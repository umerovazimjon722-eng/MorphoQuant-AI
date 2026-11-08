import csv
import json

import pytest

from morphoquant.study_analysis import compare_groups_from_csv


def write_input(path, rows):
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["animal_id", "group", "field_area_um2"])
        writer.writeheader()
        writer.writerows(rows)


def test_compare_groups_aggregates_fields_before_inference(tmp_path):
    source = tmp_path / "fields.csv"
    sample_output = tmp_path / "animals.csv"
    report_output = tmp_path / "comparison.json"
    write_input(source, [
        {"animal_id": "C1", "group": "control", "field_area_um2": 10},
        {"animal_id": "C1", "group": "control", "field_area_um2": 12},
        {"animal_id": "C2", "group": "control", "field_area_um2": 11},
        {"animal_id": "C3", "group": "control", "field_area_um2": 9},
        {"animal_id": "M1", "group": "metabolic", "field_area_um2": 20},
        {"animal_id": "M1", "group": "metabolic", "field_area_um2": 22},
        {"animal_id": "M2", "group": "metabolic", "field_area_um2": 21},
        {"animal_id": "M3", "group": "metabolic", "field_area_um2": 19},
    ])
    report = compare_groups_from_csv(
        source, sample_output, report_output,
        biological_unit_column="animal_id", group_column="group",
        measurement_column="field_area_um2", group_a="control",
        group_b="metabolic", aggregation="mean", method="welch",
    )
    assert report["design"]["n_input_subsample_rows"] == 8
    assert report["design"]["n_biological_units_total_selected"] == 6
    assert report["groups"]["control"]["n"] == 3
    assert report["groups"]["metabolic"]["n"] == 3
    with sample_output.open(encoding="utf-8", newline="") as source_file:
        rows = list(csv.DictReader(source_file))
    assert len(rows) == 6
    assert next(row for row in rows if row["animal_id"] == "C1")["field_area_um2"] == "11.0"
    saved = json.loads(report_output.read_text(encoding="utf-8"))
    assert saved["input"]["sha256"] == report["input"]["sha256"]


def test_compare_groups_median_aggregation_and_other_groups_disclosure(tmp_path):
    source = tmp_path / "fields.csv"
    write_input(source, [
        {"animal_id": "C1", "group": "control", "field_area_um2": 1},
        {"animal_id": "C1", "group": "control", "field_area_um2": 100},
        {"animal_id": "C2", "group": "control", "field_area_um2": 2},
        {"animal_id": "C3", "group": "control", "field_area_um2": 3},
        {"animal_id": "T1", "group": "treated", "field_area_um2": 10},
        {"animal_id": "T2", "group": "treated", "field_area_um2": 11},
        {"animal_id": "T3", "group": "treated", "field_area_um2": 12},
        {"animal_id": "X1", "group": "other", "field_area_um2": 99},
    ])
    report = compare_groups_from_csv(
        source, tmp_path / "sample.csv", tmp_path / "report.json",
        biological_unit_column="animal_id", group_column="group",
        measurement_column="field_area_um2", group_a="control",
        group_b="treated", aggregation="median", method="mannwhitney",
    )
    assert report["groups"]["control"]["n"] == 3
    assert report["design"]["other_groups_excluded_from_this_comparison"] == ["other"]
    assert report["comparison"]["method"] == "mannwhitney"


def test_compare_groups_rejects_too_few_biological_replicates(tmp_path):
    source = tmp_path / "fields.csv"
    write_input(source, [
        {"animal_id": "C1", "group": "control", "field_area_um2": 1},
        {"animal_id": "C2", "group": "control", "field_area_um2": 2},
        {"animal_id": "T1", "group": "treated", "field_area_um2": 3},
    ])
    with pytest.raises(ValueError, match="at least two independent"):
        compare_groups_from_csv(
            source, tmp_path / "sample.csv", tmp_path / "report.json",
            biological_unit_column="animal_id", group_column="group",
            measurement_column="field_area_um2", group_a="control", group_b="treated",
        )


@pytest.mark.parametrize("rows", [
    [{"animal_id": "", "group": "control", "field_area_um2": 1}],
    [{"animal_id": "C1", "group": "control", "field_area_um2": ""}],
    [{"animal_id": "C1", "group": "control", "field_area_um2": "not-a-number"}],
])
def test_compare_groups_rejects_invalid_input_rows(tmp_path, rows):
    source = tmp_path / "fields.csv"
    write_input(source, rows)
    with pytest.raises(ValueError):
        compare_groups_from_csv(
            source, tmp_path / "sample.csv", tmp_path / "report.json",
            biological_unit_column="animal_id", group_column="group",
            measurement_column="field_area_um2", group_a="control", group_b="treated",
        )


def test_compare_groups_rejects_path_collisions(tmp_path):
    source = tmp_path / "fields.csv"
    write_input(source, [
        {"animal_id": "C1", "group": "control", "field_area_um2": 1},
        {"animal_id": "C2", "group": "control", "field_area_um2": 2},
        {"animal_id": "T1", "group": "treated", "field_area_um2": 3},
        {"animal_id": "T2", "group": "treated", "field_area_um2": 4},
    ])
    with pytest.raises(ValueError, match="different paths"):
        compare_groups_from_csv(
            source, tmp_path / "same.csv", tmp_path / "same.csv",
            biological_unit_column="animal_id", group_column="group",
            measurement_column="field_area_um2", group_a="control", group_b="treated",
        )
