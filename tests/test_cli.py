import csv
import json

import numpy as np
from PIL import Image
import tifffile

from morphoquant.cli import main


def test_cli_measures_mask_and_writes_csv(tmp_path, capsys):
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[2:8, 3:13] = 255
    source = tmp_path / "mask.png"
    output = tmp_path / "results" / "measurements.csv"
    Image.fromarray(mask, mode="L").save(source)

    exit_code = main(
        [
            "measure-mask",
            str(source),
            "--micrometers-per-pixel",
            "0.5",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert "Measured 1 connected component(s)" in capsys.readouterr().out
    with output.open(encoding="utf-8", newline="") as csv_file:
        row = next(csv.DictReader(csv_file))
    assert row["area_px2"] == "60"
    assert float(row["area_um2"]) == 15.0
    assert float(row["pixel_size_x_um"]) == 0.5
    assert float(row["pixel_size_y_um"]) == 0.5
    metadata_path = output.with_name("measurements.metadata.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["segmentation_performed"] is False
    assert metadata["results"]["component_count"] == 1


def test_cli_writes_header_when_mask_has_no_foreground(tmp_path):
    mask = np.zeros((10, 10), dtype=np.uint8)
    source = tmp_path / "empty.png"
    output = tmp_path / "empty.csv"
    Image.fromarray(mask, mode="L").save(source)

    assert main(
        [
            "measure-mask",
            str(source),
            "--micrometers-per-pixel",
            "1",
            "--output",
            str(output),
        ]
    ) == 0
    assert output.is_file()
    assert output.with_name("empty.metadata.json").is_file()


def test_cli_refuses_to_overwrite_input_mask(tmp_path):
    import pytest

    source = tmp_path / "mask.png"
    original = np.zeros((8, 8), dtype=np.uint8)
    Image.fromarray(original, mode="L").save(source)
    original_bytes = source.read_bytes()

    with pytest.raises(SystemExit):
        main(
            [
                "measure-mask",
                str(source),
                "--micrometers-per-pixel",
                "1",
                "--output",
                str(source),
            ]
        )

    assert source.read_bytes() == original_bytes

def test_cli_summarizes_labeled_mask_and_writes_provenance(tmp_path, capsys):
    mask = np.zeros((20, 30), dtype=np.uint8)
    mask[2:12, 2:22] = 1
    mask[14:19, 23:28] = 2
    source = tmp_path / "zones.png"
    output = tmp_path / "zone-results.csv"
    names = tmp_path / "classes.json"
    Image.fromarray(mask, mode="L").save(source)
    names.write_text(json.dumps({"1": "cortex", "2": "medulla"}), encoding="utf-8")

    result = main(
        [
            "measure-labels",
            str(source),
            "--micrometers-per-pixel-x",
            "0.5",
            "--micrometers-per-pixel-y",
            "1.0",
            "--class-names",
            str(names),
            "--output",
            str(output),
        ]
    )

    assert result == 0
    assert "Summarized 2 annotation class(es)" in capsys.readouterr().out
    with output.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert [row["class_name"] for row in rows] == ["cortex", "medulla"]
    assert float(rows[0]["area_um2"]) == 100.0
    metadata = json.loads(
        output.with_name("zone-results.metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["segmentation_performed"] is False
    assert metadata["results"]["class_count"] == 2
    assert metadata["input_mask"]["class_names"] == {"1": "cortex", "2": "medulla"}


def test_cli_rejects_invalid_class_name_json(tmp_path):
    mask = np.zeros((8, 8), dtype=np.uint8)
    source = tmp_path / "labels.png"
    names = tmp_path / "classes.json"
    Image.fromarray(mask, mode="L").save(source)
    names.write_text('["not", "an", "object"]', encoding="utf-8")

    import pytest
    with pytest.raises(SystemExit):
        main(
            [
                "measure-labels",
                str(source),
                "--micrometers-per-pixel",
                "1",
                "--class-names",
                str(names),
                "--output",
                str(tmp_path / "out.csv"),
            ]
        )


def test_cli_uses_ome_tiff_calibration_and_records_source(tmp_path):
    mask = np.zeros((12, 18), dtype=np.uint8)
    mask[2:8, 3:13] = 255
    source = tmp_path / "calibrated-mask.ome.tif"
    output = tmp_path / "ome-results.csv"
    tifffile.imwrite(
        source,
        mask,
        ome=True,
        metadata={
            "axes": "YX",
            "PhysicalSizeX": 0.5,
            "PhysicalSizeXUnit": "µm",
            "PhysicalSizeY": 0.75,
            "PhysicalSizeYUnit": "µm",
        },
    )

    result = main(
        [
            "measure-mask",
            str(source),
            "--use-tiff-metadata",
            "--output",
            str(output),
        ]
    )

    assert result == 0
    with output.open(encoding="utf-8", newline="") as csv_file:
        row = next(csv.DictReader(csv_file))
    assert float(row["area_um2"]) == 60 * 0.5 * 0.75
    metadata = json.loads(
        output.with_name("ome-results.metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["calibration"]["pixel_size_x_um"] == 0.5
    assert metadata["calibration"]["pixel_size_y_um"] == 0.75
    assert "TIFF/OME-TIFF metadata" in metadata["calibration"]["source"]


def test_cli_rejects_mixing_tiff_metadata_and_manual_calibration(tmp_path):
    mask = np.zeros((8, 8), dtype=np.uint8)
    source = tmp_path / "plain.tif"
    tifffile.imwrite(source, mask)

    import pytest
    with pytest.raises(SystemExit):
        main(
            [
                "measure-mask",
                str(source),
                "--use-tiff-metadata",
                "--micrometers-per-pixel",
                "1",
                "--output",
                str(tmp_path / "out.csv"),
            ]
        )


def test_cli_creates_visual_overlay_for_annotated_tissue_zones(tmp_path, capsys):
    image = np.full((18, 24, 3), 150, dtype=np.uint8)
    labels = np.zeros((18, 24), dtype=np.uint8)
    labels[2:10, 2:15] = 1
    labels[11:16, 17:22] = 2
    image_path = tmp_path / "original.png"
    mask_path = tmp_path / "labels.png"
    names_path = tmp_path / "classes.json"
    output = tmp_path / "qc" / "overlay.png"
    Image.fromarray(image, mode="RGB").save(image_path)
    Image.fromarray(labels, mode="L").save(mask_path)
    names_path.write_text(json.dumps({"1": "cortex", "2": "medulla"}), encoding="utf-8")

    result = main([
        "overlay-labels", str(image_path), str(mask_path),
        "--class-names", str(names_path), "--alpha", "0.4",
        "--output", str(output),
    ])

    assert result == 0
    assert output.is_file()
    assert "visual quality-control preview" in capsys.readouterr().out


def test_cli_overlay_refuses_to_overwrite_source_image(tmp_path):
    import pytest

    image = np.zeros((8, 8, 3), dtype=np.uint8)
    labels = np.zeros((8, 8), dtype=np.uint8)
    image_path = tmp_path / "original.png"
    mask_path = tmp_path / "labels.png"
    Image.fromarray(image, mode="RGB").save(image_path)
    Image.fromarray(labels, mode="L").save(mask_path)
    original_bytes = image_path.read_bytes()

    with pytest.raises(SystemExit):
        main([
            "overlay-labels", str(image_path), str(mask_path),
            "--output", str(image_path),
        ])

    assert image_path.read_bytes() == original_bytes


def test_cli_compares_groups_after_sample_level_aggregation(tmp_path, capsys):
    source = tmp_path / "field-measurements.csv"
    with source.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["animal", "group", "cortical_area"])
        writer.writeheader()
        writer.writerows([
            {"animal": "C1", "group": "control", "cortical_area": 10},
            {"animal": "C1", "group": "control", "cortical_area": 12},
            {"animal": "C2", "group": "control", "cortical_area": 11},
            {"animal": "C3", "group": "control", "cortical_area": 9},
            {"animal": "M1", "group": "metabolic", "cortical_area": 20},
            {"animal": "M1", "group": "metabolic", "cortical_area": 22},
            {"animal": "M2", "group": "metabolic", "cortical_area": 21},
            {"animal": "M3", "group": "metabolic", "cortical_area": 19},
        ])
    sample_output = tmp_path / "animal-level.csv"
    report_output = tmp_path / "comparison.json"
    result = main([
        "compare-groups", "--input", str(source),
        "--biological-unit-column", "animal", "--group-column", "group",
        "--measurement-column", "cortical_area",
        "--group-a", "control", "--group-b", "metabolic",
        "--method", "welch",
        "--sample-level-output", str(sample_output),
        "--report-output", str(report_output),
    ])
    assert result == 0
    assert sample_output.is_file()
    assert report_output.is_file()
    assert "Compared 3 vs 3 biological units" in capsys.readouterr().out
    with sample_output.open(encoding="utf-8", newline="") as sample_file:
        assert len(list(csv.DictReader(sample_file))) == 6


def test_cli_compare_groups_refuses_to_overwrite_input(tmp_path):
    import pytest
    source = tmp_path / "measurements.csv"
    with source.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["animal", "group", "value"])
        writer.writeheader()
        writer.writerows([
            {"animal": "A1", "group": "a", "value": 1},
            {"animal": "A2", "group": "a", "value": 2},
            {"animal": "B1", "group": "b", "value": 3},
            {"animal": "B2", "group": "b", "value": 4},
        ])
    original = source.read_bytes()
    with pytest.raises(SystemExit):
        main([
            "compare-groups", "--input", str(source),
            "--biological-unit-column", "animal", "--group-column", "group",
            "--measurement-column", "value", "--group-a", "a", "--group-b", "b",
            "--sample-level-output", str(source),
            "--report-output", str(tmp_path / "report.json"),
        ])
    assert source.read_bytes() == original


def test_cli_measures_ome_tiff_3d_label_volume_and_writes_provenance(tmp_path, capsys):
    import tifffile

    labels = np.zeros((5, 12, 14), dtype=np.uint8)
    labels[1:4, 2:7, 3:9] = 1
    source = tmp_path / "adrenal-volume.ome.tif"
    output = tmp_path / "volume-summary.csv"
    names = tmp_path / "classes.json"
    tifffile.imwrite(
        source,
        labels,
        ome=True,
        metadata={
            "axes": "ZYX",
            "PhysicalSizeX": 0.25,
            "PhysicalSizeXUnit": "µm",
            "PhysicalSizeY": 0.5,
            "PhysicalSizeYUnit": "µm",
            "PhysicalSizeZ": 2.0,
            "PhysicalSizeZUnit": "µm",
        },
    )
    names.write_text(json.dumps({"1": "cortex"}), encoding="utf-8")

    result = main([
        "measure-volume", str(source),
        "--class-names", str(names),
        "--output", str(output),
    ])

    assert result == 0
    assert "Measured 1 3D annotation class(es)" in capsys.readouterr().out
    with output.open(encoding="utf-8", newline="") as stream:
        row = next(csv.DictReader(stream))
    assert row["class_name"] == "cortex"
    assert int(row["voxel_count"]) == 90
    assert float(row["volume_um3"]) == pytest.approx(22.5)
    metadata = json.loads(
        output.with_name("volume-summary.metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["calibration"]["voxel_size_z_um"] == 2.0
    assert metadata["measurement_parameters"]["connectivity"] == 26


def test_cli_measure_volume_rejects_missing_z_calibration(tmp_path):
    import tifffile
    import pytest

    labels = np.zeros((4, 8, 9), dtype=np.uint8)
    source = tmp_path / "no-z.ome.tif"
    tifffile.imwrite(
        source,
        labels,
        ome=True,
        metadata={
            "axes": "ZYX",
            "PhysicalSizeX": 0.25,
            "PhysicalSizeXUnit": "µm",
            "PhysicalSizeY": 0.25,
            "PhysicalSizeYUnit": "µm",
        },
    )
    with pytest.raises(SystemExit):
        main([
            "measure-volume", str(source),
            "--output", str(tmp_path / "out.csv"),
        ])
