"""Machine-readable provenance for reproducible morphometric analyses."""

from datetime import datetime, timezone
import hashlib
import json
from numbers import Integral
from pathlib import Path
from typing import Mapping, Union

from . import __version__
from .calibration import MicroscopeCalibration

PathLike = Union[str, Path]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_analysis_metadata(
    *,
    input_mask_path: PathLike,
    output_csv_path: PathLike,
    calibration: MicroscopeCalibration,
    mask_shape: tuple[int, int],
    foreground: str,
    threshold: float | None,
    min_area_px: int,
    measurement_count: int,
    metadata_path: PathLike | None = None,
    analysis_type: str = "2D connected-component morphometry of a researcher-provided binary mask",
    label_names: Mapping[int, str] | None = None,
) -> Path:
    """Write a JSON sidecar recording inputs, parameters, units, and checksums.

    File names are recorded instead of absolute paths to avoid exposing local
    directory names. SHA-256 values allow downstream users to verify that the
    analyzed mask and exported CSV have not changed.
    """
    input_path = Path(input_mask_path)
    output_path = Path(output_csv_path)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input mask does not exist: {input_path}")
    if not output_path.is_file():
        raise FileNotFoundError(f"Output CSV does not exist: {output_path}")
    if len(mask_shape) != 2 or any(int(size) < 1 for size in mask_shape):
        raise ValueError("mask_shape must contain two positive dimensions.")
    if foreground not in ("bright", "dark"):
        raise ValueError("foreground must be either 'bright' or 'dark'.")
    if not isinstance(analysis_type, str) or not analysis_type.strip():
        raise ValueError("analysis_type must be a non-empty string.")
    if label_names is not None:
        if not isinstance(label_names, Mapping):
            raise TypeError("label_names must be a mapping.")
        if any(
            isinstance(key, bool) or not isinstance(key, Integral)
            or not isinstance(value, str) or not value.strip()
            for key, value in label_names.items()
        ):
            raise ValueError("label_names must map integer IDs to non-empty strings.")
    if isinstance(min_area_px, bool) or not isinstance(min_area_px, Integral) or min_area_px < 1:
        raise ValueError("min_area_px must be a positive integer.")
    if (
        isinstance(measurement_count, bool)
        or not isinstance(measurement_count, Integral)
        or measurement_count < 0
    ):
        raise ValueError("measurement_count must be a non-negative integer.")

    destination = (
        Path(metadata_path)
        if metadata_path is not None
        else output_path.with_name(f"{output_path.stem}.metadata.json")
    )
    if destination.resolve() in {input_path.resolve(), output_path.resolve()}:
        raise ValueError("Metadata output must not overwrite the input mask or result CSV.")
    destination.parent.mkdir(parents=True, exist_ok=True)

    metadata = {
        "metadata_schema_version": "1.0",
        "software": "MorphoQuant AI",
        "software_version": __version__,
        "analysis": analysis_type.strip(),
        "segmentation_performed": False,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_mask": {
            "file_name": input_path.name,
            "sha256": _sha256(input_path),
            "shape_rows_columns": [int(mask_shape[0]), int(mask_shape[1])],
            "foreground": foreground,
            "threshold": threshold,
            "class_names": {str(key): value for key, value in label_names.items()} if label_names is not None else None,
            "threshold_rule": (
                "pixel > threshold" if foreground == "bright" else "pixel < threshold"
            ) if threshold is not None else "two-level mask; selected extreme intensity",
        },
        "calibration": {
            "pixel_size_x_um": calibration.scale_x_um,
            "pixel_size_y_um": calibration.scale_y_um,
            "isotropic": calibration.is_isotropic,
            "source": "user-supplied; verify against calibrated scale bar or acquisition metadata",
        },
        "measurement_parameters": {
            "connectivity": 8,
            "minimum_component_area_px": min_area_px,
            "perimeter_method": "0.5-level marching-squares contour; axis-specific physical spacing",
        },
        "results": {
            "component_count": measurement_count,
            "csv_file_name": output_path.name,
            "csv_sha256": _sha256(output_path),
        },
        "limitations": [
            "The software does not perform tissue or cell segmentation or infer class labels.",
            "The input mask must be reviewed and validated by the researcher.",
            "Synthetic unit tests do not establish biological or clinical validity.",
            "Perimeter is a digital contour estimate affected by image resolution and boundary discretization.",
        ],
    }

    temporary = destination.with_name(destination.name + ".tmp")
    try:
        temporary.write_text(
            json.dumps(metadata, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()

    return destination
