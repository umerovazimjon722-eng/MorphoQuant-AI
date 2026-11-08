"""End-to-end CSV comparison with biological-unit aggregation."""
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Dict, Iterable, Literal, Union

from .statistical_analysis import aggregate_subsamples_by_unit, compare_independent_groups, describe_samples

PathLike = Union[str, Path]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare_groups_from_csv(
    input_csv: PathLike,
    sample_level_csv: PathLike,
    report_json: PathLike,
    *,
    biological_unit_column: str,
    group_column: str,
    measurement_column: str,
    group_a: str,
    group_b: str,
    aggregation: Literal["mean", "median"] = "mean",
    method: Literal["welch", "mannwhitney"] = "welch",
    confidence_level: float = 0.95,
) -> Dict[str, object]:
    """Aggregate subsamples to biological units, compare two groups, and save auditable outputs.

    Input rows must represent fields, sections, or other subsamples. Rows with
    the same biological-unit ID are aggregated before inferential statistics.
    Only the two explicitly selected groups are compared. Other groups are
    excluded and disclosed. One outcome is analyzed; this function does not
    perform multiple-outcome correction, assumption checks, or mixed models.
    """
    source = Path(input_csv)
    sample_path = Path(sample_level_csv)
    report_path = Path(report_json)
    if not source.is_file():
        raise FileNotFoundError(f"Input CSV does not exist: {source}")
    source_resolved, sample_resolved, report_resolved = (
        source.resolve(), sample_path.resolve(), report_path.resolve()
    )
    if sample_resolved == report_resolved:
        raise ValueError("Sample-level CSV and JSON report must have different paths.")
    if source_resolved in {sample_resolved, report_resolved}:
        raise ValueError("Outputs must not overwrite the input data CSV.")

    columns = (biological_unit_column, group_column, measurement_column)
    if any(not isinstance(value, str) or not value.strip() for value in columns):
        raise ValueError("CSV column names must be non-empty strings.")
    if len(set(columns)) != 3:
        raise ValueError("Biological-unit, group, and measurement columns must be distinct.")
    if not isinstance(group_a, str) or not group_a.strip():
        raise ValueError("group_a must be a non-empty string.")
    if not isinstance(group_b, str) or not group_b.strip():
        raise ValueError("group_b must be a non-empty string.")
    group_a, group_b = group_a.strip(), group_b.strip()
    if group_a == group_b:
        raise ValueError("group_a and group_b must be different.")
    if aggregation not in ("mean", "median"):
        raise ValueError("aggregation must be 'mean' or 'median'.")
    if method not in ("welch", "mannwhitney"):
        raise ValueError("method must be 'welch' or 'mannwhitney'.")
    if isinstance(confidence_level, bool) or not isinstance(confidence_level, (int, float)):
        raise TypeError("confidence_level must be numeric.")
    if not math.isfinite(float(confidence_level)) or not 0 < float(confidence_level) < 1:
        raise ValueError("confidence_level must be finite and between 0 and 1.")

    records = []
    try:
        with source.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            headers = reader.fieldnames
            if not headers:
                raise ValueError("Input CSV is empty or has no header row.")
            if len(set(headers)) != len(headers):
                raise ValueError("Input CSV contains duplicate column names.")
            missing = set(columns).difference(headers)
            if missing:
                raise ValueError("Input CSV is missing required columns: " + ", ".join(sorted(missing)))
            for row_number, row in enumerate(reader, start=2):
                unit = (row.get(biological_unit_column) or "").strip()
                group = (row.get(group_column) or "").strip()
                raw = (row.get(measurement_column) or "").strip()
                if not unit:
                    raise ValueError(f"Row {row_number} has a missing biological-unit identifier.")
                if not group:
                    raise ValueError(f"Row {row_number} has a missing group label.")
                if not raw:
                    raise ValueError(f"Row {row_number} has a missing measurement.")
                try:
                    value = float(raw)
                except ValueError as exc:
                    raise ValueError(f"Row {row_number} has a non-numeric measurement: {raw!r}.") from exc
                if not math.isfinite(value):
                    raise ValueError(f"Row {row_number} has a non-finite measurement.")
                records.append({
                    biological_unit_column: unit,
                    group_column: group,
                    measurement_column: value,
                })
    except UnicodeDecodeError as exc:
        raise ValueError("Input CSV is not valid UTF-8 text.") from exc

    if not records:
        raise ValueError("Input CSV contains no measurement rows.")

    sample_records = aggregate_subsamples_by_unit(
        records,
        biological_unit_key=biological_unit_column,
        measurement_key=measurement_column,
        group_key=group_column,
        aggregation=aggregation,
    )
    present_groups = sorted({str(row[group_column]) for row in sample_records})
    for selected_group in (group_a, group_b):
        if selected_group not in present_groups:
            raise ValueError(
                f"Selected group {selected_group!r} was not found. "
                f"Available groups: {', '.join(present_groups)}."
            )

    selected = [
        row for row in sample_records
        if row[group_column] in (group_a, group_b)
    ]
    values_a = [float(row[measurement_column]) for row in selected if row[group_column] == group_a]
    values_b = [float(row[measurement_column]) for row in selected if row[group_column] == group_b]
    summary_a = describe_samples(values_a)
    summary_b = describe_samples(values_b)
    comparison = compare_independent_groups(
        values_a, values_b, method=method, confidence_level=float(confidence_level)
    )

    sample_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    sample_fields = (
        biological_unit_column, group_column, measurement_column,
        "n_subsamples", "aggregation",
    )
    temporary_csv = sample_path.with_name(sample_path.name + ".tmp")
    try:
        with temporary_csv.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=sample_fields)
            writer.writeheader()
            writer.writerows(selected)
        temporary_csv.replace(sample_path)
    finally:
        if temporary_csv.exists():
            temporary_csv.unlink()

    other_groups = sorted(set(present_groups).difference({group_a, group_b}))
    report: Dict[str, object] = {
        "report_schema_version": "1.0",
        "software": "MorphoQuant AI",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": {
            "file_name": source.name,
            "sha256": _sha256(source),
            "row_definition": "one row per field, section, or other subsample",
        },
        "design": {
            "biological_unit_column": biological_unit_column,
            "group_column": group_column,
            "measurement_column": measurement_column,
            "aggregation": aggregation,
            "independent_groups": [group_a, group_b],
            "other_groups_excluded_from_this_comparison": other_groups,
            "n_biological_units_total_selected": len(selected),
            "n_input_subsample_rows": len(records),
        },
        "groups": {group_a: summary_a, group_b: summary_b},
        "comparison": comparison,
        "outputs": {
            "sample_level_csv": sample_path.name,
            "sample_level_csv_sha256": _sha256(sample_path),
        },
        "interpretation_notes": [
            "Each row in the inferential comparison represents one biological unit.",
            "Subsamples were aggregated before group comparison.",
            "The aggregation rule must be justified in the study protocol.",
            "Welch or Mann-Whitney selection is the researcher's responsibility.",
            "Assumptions, outliers, missingness, and study design require independent review.",
            "This report analyzes one outcome; no multiple-outcome correction was applied.",
            "Statistical significance does not establish biological or clinical importance.",
        ],
    }
    temporary_json = report_path.with_name(report_path.name + ".tmp")
    try:
        temporary_json.write_text(
            json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary_json.replace(report_path)
    finally:
        if temporary_json.exists():
            temporary_json.unlink()
    return report
