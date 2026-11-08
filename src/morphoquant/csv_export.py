"""CSV export helpers for morphometric measurements."""

import csv
from pathlib import Path
from typing import Iterable, Mapping, Union

PathLike = Union[str, Path]

MEASUREMENT_COLUMNS = (
    "label",
    "area_px2",
    "area_um2",
    "perimeter_px",
    "perimeter_um",
    "equivalent_diameter_um",
    "centroid_x_px",
    "centroid_y_px",
    "centroid_x_um",
    "centroid_y_um",
    "pixel_size_x_um",
    "pixel_size_y_um",
    "eccentricity",
    "solidity",
)


def write_measurements_csv(
    measurements: Iterable[Mapping[str, object]],
    path: PathLike,
) -> Path:
    """Write measurements using a stable, documented column order.

    Empty measurement collections produce a header-only CSV. The destination
    parent directory is created when necessary.
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = list(measurements)
    for index, row in enumerate(rows):
        missing = set(MEASUREMENT_COLUMNS).difference(row)
        if missing:
            raise ValueError(
                f"Measurement row {index} is missing required fields: "
                + ", ".join(sorted(missing))
            )

    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=MEASUREMENT_COLUMNS,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)

    return output_path


LABELED_MEASUREMENT_COLUMNS = (
    "class_id",
    "class_name",
    "component_count",
    "area_px2",
    "area_um2",
    "foreground_area_percent",
    "mean_component_area_um2",
    "median_component_area_um2",
    "mean_equivalent_diameter_um",
    "total_perimeter_px",
    "total_perimeter_um",
    "area_weighted_centroid_x_um",
    "area_weighted_centroid_y_um",
    "mean_component_eccentricity",
    "mean_component_solidity",
    "pixel_size_x_um",
    "pixel_size_y_um",
)


def write_labeled_measurements_csv(
    measurements: Iterable[Mapping[str, object]],
    path: PathLike,
) -> Path:
    """Write class-wise tissue measurements with a stable CSV column order."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = list(measurements)
    for index, row in enumerate(rows):
        missing = set(LABELED_MEASUREMENT_COLUMNS).difference(row)
        if missing:
            raise ValueError(
                f"Labeled measurement row {index} is missing required fields: "
                + ", ".join(sorted(missing))
            )

    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=LABELED_MEASUREMENT_COLUMNS,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)

    return output_path
