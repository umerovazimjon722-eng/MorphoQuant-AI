"""Command-line interface for reproducible mask-based morphometry."""

import argparse
import json
from pathlib import Path
from typing import Dict, Sequence

from . import __version__
from .calibration import MicroscopeCalibration
from .csv_export import write_labeled_measurements_csv, write_measurements_csv
from .labeled_morphometry import measure_labeled_mask
from .masks import load_binary_mask, load_labeled_mask
from .morphometry import measure_binary_mask
from .provenance import write_analysis_metadata


def _add_calibration_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--micrometers-per-pixel",
        type=float,
        default=None,
        help="isotropic pixel size in micrometres per pixel",
    )
    parser.add_argument(
        "--micrometers-per-pixel-x",
        type=float,
        default=None,
        help="horizontal pixel size in micrometres per pixel (use with the y value)",
    )
    parser.add_argument(
        "--micrometers-per-pixel-y",
        type=float,
        default=None,
        help="vertical pixel size in micrometres per pixel (use with the x value)",
    )


def _build_calibration(args: argparse.Namespace) -> MicroscopeCalibration:
    return MicroscopeCalibration(
        micrometers_per_pixel=args.micrometers_per_pixel,
        micrometers_per_pixel_x=args.micrometers_per_pixel_x,
        micrometers_per_pixel_y=args.micrometers_per_pixel_y,
    )


def _validate_output_paths(
    input_path: Path,
    output_path: Path,
    metadata_path: Path | None,
) -> None:
    input_resolved = input_path.resolve()
    output_resolved = output_path.resolve()
    metadata_resolved = metadata_path.resolve() if metadata_path is not None else None

    if input_resolved == output_resolved:
        raise ValueError("The output CSV path must not overwrite the input mask.")
    if metadata_resolved is not None and metadata_resolved in {
        input_resolved,
        output_resolved,
    }:
        raise ValueError(
            "The metadata JSON path must differ from the input mask and output CSV."
        )


def _load_class_names(path: Path | None) -> Dict[int, str] | None:
    if path is None:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read class names JSON: {path}") from exc

    if not isinstance(data, dict):
        raise ValueError("Class names JSON must be an object mapping integer IDs to names.")

    names: Dict[int, str] = {}
    for key, value in data.items():
        try:
            class_id = int(key)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Class ID {key!r} is not an integer.") from exc
        if str(class_id) != str(key).strip():
            raise ValueError(f"Class ID {key!r} must use canonical integer notation.")
        if class_id in names:
            raise ValueError(f"Duplicate class ID: {class_id}.")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Class name for ID {class_id} must be a non-empty string.")
        names[class_id] = value.strip()
    return names


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="morphoquant",
        description=(
            "Reproducible quantitative histology tools for researcher-prepared masks. "
            "No automatic segmentation or clinical diagnosis is performed."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    measure = subparsers.add_parser(
        "measure-mask",
        help="measure connected components in a grayscale binary mask",
    )
    measure.add_argument("mask", type=Path, help="path to a grayscale binary mask")
    _add_calibration_arguments(measure)
    measure.add_argument("--output", type=Path, required=True, help="destination CSV file")
    measure.add_argument(
        "--metadata-output",
        type=Path,
        default=None,
        help="optional provenance JSON path (default: <output-stem>.metadata.json)",
    )
    measure.add_argument(
        "--min-area-px",
        type=int,
        default=1,
        help="minimum connected-component area in pixels (default: 1)",
    )
    measure.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="explicit grayscale threshold; required for non-binary masks",
    )
    measure.add_argument(
        "--foreground",
        choices=("bright", "dark"),
        default="bright",
        help="which mask intensity is foreground (default: bright)",
    )

    labeled = subparsers.add_parser(
        "measure-labels",
        help="summarize class-wise morphometry in a researcher-annotated label image",
    )
    labeled.add_argument("mask", type=Path, help="path to a grayscale integer label image")
    _add_calibration_arguments(labeled)
    labeled.add_argument("--output", type=Path, required=True, help="destination class-summary CSV")
    labeled.add_argument(
        "--metadata-output",
        type=Path,
        default=None,
        help="optional provenance JSON path (default: <output-stem>.metadata.json)",
    )
    labeled.add_argument(
        "--class-names",
        type=Path,
        default=None,
        help='optional JSON mapping, e.g. {"1": "cortex", "2": "medulla"}',
    )
    labeled.add_argument(
        "--background-label",
        type=int,
        default=0,
        help="integer label representing background (default: 0)",
    )
    labeled.add_argument(
        "--min-area-px",
        type=int,
        default=1,
        help="minimum connected component area in pixels (default: 1)",
    )

    return parser


def _run_binary_analysis(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        _validate_output_paths(args.mask, args.output, args.metadata_output)
        calibration = _build_calibration(args)
        mask = load_binary_mask(
            args.mask,
            threshold=args.threshold,
            foreground=args.foreground,
        )
        measurements = measure_binary_mask(
            mask,
            calibration,
            min_area_px=args.min_area_px,
        )
        output_path = write_measurements_csv(measurements, args.output)
        metadata_path = write_analysis_metadata(
            input_mask_path=args.mask,
            output_csv_path=output_path,
            calibration=calibration,
            mask_shape=mask.shape,
            foreground=args.foreground,
            threshold=args.threshold,
            min_area_px=args.min_area_px,
            measurement_count=len(measurements),
            metadata_path=args.metadata_output,
            analysis_type="2D connected-component morphometry of a researcher-provided binary mask",
        )
    except (FileNotFoundError, TypeError, ValueError, OSError) as exc:
        parser.error(str(exc))

    print(
        f"Measured {len(measurements)} connected component(s); "
        f"wrote {output_path} and provenance {metadata_path}."
    )
    return 0


def _run_labeled_analysis(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        _validate_output_paths(args.mask, args.output, args.metadata_output)
        calibration = _build_calibration(args)
        mask = load_labeled_mask(args.mask)
        class_names = _load_class_names(args.class_names)
        measurements = measure_labeled_mask(
            mask,
            calibration,
            background_label=args.background_label,
            label_names=class_names,
            min_component_area_px=args.min_area_px,
        )
        output_path = write_labeled_measurements_csv(measurements, args.output)
        metadata_path = write_analysis_metadata(
            input_mask_path=args.mask,
            output_csv_path=output_path,
            calibration=calibration,
            mask_shape=mask.shape,
            foreground=None,
            threshold=None,
            min_area_px=args.min_area_px,
            measurement_count=len(measurements),
            metadata_path=args.metadata_output,
            analysis_type=(
                "2D class-wise morphometry of a researcher-annotated integer label mask"
            ),
            label_names=class_names,
            result_count_label="class_count",
        )
    except (FileNotFoundError, TypeError, ValueError, OSError) as exc:
        parser.error(str(exc))

    print(
        f"Summarized {len(measurements)} annotation class(es); "
        f"wrote {output_path} and provenance {metadata_path}."
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI. argv is injectable for tests."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "measure-mask":
        return _run_binary_analysis(args, parser)
    if args.command == "measure-labels":
        return _run_labeled_analysis(args, parser)

    parser.error("A command is required.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
