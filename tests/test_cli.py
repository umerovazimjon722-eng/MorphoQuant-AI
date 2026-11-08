import csv

import numpy as np
from PIL import Image

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
    metadata = __import__("json").loads(metadata_path.read_text(encoding="utf-8"))
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
