"""Command-line interface for reproducible mask-based morphometry."""

import argparse
import json
from pathlib import Path
from typing import Dict, Sequence

from . import __version__
from .calibration import MicroscopeCalibration, VoxelCalibration
from .csv_export import write_labeled_measurements_csv, write_measurements_csv, write_volume_measurements_csv
from .labeled_morphometry import measure_labeled_mask
from .image_io import load_rgb_image, load_labeled_volume_tiff
from .masks import load_binary_mask, load_labeled_mask
from .morphometry import measure_binary_mask
from .provenance import write_analysis_metadata
from .tiff_metadata import read_tiff_metadata
from .study_analysis import compare_groups_from_csv
from .visualization import save_label_overlay
from .volume_morphometry import measure_labeled_volume


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
        "--use-tiff-metadata",
        action="store_true",
        help="read calibrated X/Y pixel sizes from TIFF/OME-TIFF metadata",
    )
    parser.add_argument(
        "--micrometers-per-pixel-y",
        type=float,
        default=None,
        help="vertical pixel size in micrometres per pixel (use with the x value)",
    )


def _build_calibration(args: argparse.Namespace) -> MicroscopeCalibration:
    supplied_scales = (
        args.micrometers_per_pixel,
        args.micrometers_per_pixel_x,
        args.micrometers_per_pixel_y,
    )
    if args.use_tiff_metadata:
        if any(value is not None for value in supplied_scales):
            raise ValueError(
                "Do not combine --use-tiff-metadata with manually supplied pixel sizes."
            )
        return read_tiff_metadata(args.mask).to_calibration()

    return MicroscopeCalibration(
        micrometers_per_pixel=args.micrometers_per_pixel,
        micrometers_per_pixel_x=args.micrometers_per_pixel_x,
        micrometers_per_pixel_y=args.micrometers_per_pixel_y,
    )


def _calibration_source(args: argparse.Namespace) -> str:
    if args.use_tiff_metadata:
        return "TIFF/OME-TIFF metadata; verify against acquisition records"
    return "user-supplied calibrated scale or independently measured scale bar"


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

    volume = subparsers.add_parser(
        "measure-volume",
        help="measure class-wise 3D morphometry in a calibrated OME-TIFF ZYX label volume",
    )
    volume.add_argument("volume", type=Path, help="OME-TIFF integer label volume with axes ZYX")
    volume.add_argument("--output", type=Path, required=True, help="destination class-summary CSV")
    volume.add_argument("--metadata-output", type=Path, default=None, help="optional provenance JSON path")
    volume.add_argument("--class-names", type=Path, default=None, help="optional class-name JSON")
    volume.add_argument("--background-label", type=int, default=0)
    volume.add_argument("--min-voxels", type=int, default=1)
    volume.add_argument("--series-index", type=int, default=0)
    volume.add_argument(
        "--max-uncompressed-bytes",
        type=int,
        default=1_000_000_000,
        help="maximum allowed decoded volume size (default: 1,000,000,000 bytes)",
    )

    comparison = subparsers.add_parser(
        "compare-groups",
        help="aggregate subsamples by biological unit and compare two independent groups",
    )
    comparison.add_argument("--input", type=Path, required=True, help="tidy CSV, one row per subsample")
    comparison.add_argument("--biological-unit-column", required=True)
    comparison.add_argument("--group-column", required=True)
    comparison.add_argument("--measurement-column", required=True)
    comparison.add_argument("--group-a", required=True)
    comparison.add_argument("--group-b", required=True)
    comparison.add_argument("--aggregation", choices=("mean", "median"), default="mean")
    comparison.add_argument("--method", choices=("welch", "mannwhitney"), default="welch")
    comparison.add_argument("--confidence-level", type=float, default=0.95)
    comparison.add_argument("--sample-level-output", type=Path, required=True)
    comparison.add_argument("--report-output", type=Path, required=True)

    overlay = subparsers.add_parser(
        "overlay-labels",
        help="create a visual QC overlay for a researcher-annotated label image",
    )
    overlay.add_argument("image", type=Path, help="original microscopy image")
    overlay.add_argument("mask", type=Path, help="grayscale integer label image")
    overlay.add_argument("--output", type=Path, required=True, help="destination PNG preview")
    overlay.add_argument("--class-names", type=Path, default=None, help="optional class-name JSON")
    overlay.add_argument("--background-label", type=int, default=0)
    overlay.add_argument("--alpha", type=float, default=0.35)
    overlay.add_argument("--max-dimension", type=int, default=2400)

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
            calibration_source=_calibration_source(args),
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
            calibration_source=_calibration_source(args),
        )
    except (FileNotFoundError, TypeError, ValueError, OSError) as exc:
        parser.error(str(exc))

    print(
        f"Summarized {len(measurements)} annotation class(es); "
        f"wrote {output_path} and provenance {metadata_path}."
    )
    return 0


def _run_overlay_analysis(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        image_path = args.image.resolve()
        mask_path = args.mask.resolve()
        output_path = args.output.resolve()
        class_names_path = args.class_names.resolve() if args.class_names is not None else None
        if output_path in {image_path, mask_path}:
            raise ValueError("The overlay PNG must not overwrite the source image or label mask.")
        if class_names_path is not None and output_path == class_names_path:
            raise ValueError("The overlay PNG must not overwrite the class-names JSON.")

        image = load_rgb_image(args.image)
        mask = load_labeled_mask(args.mask)
        class_names = _load_class_names(args.class_names)
        written = save_label_overlay(
            image, mask, args.output,
            class_names=class_names,
            background_label=args.background_label,
            alpha=args.alpha,
            max_dimension=args.max_dimension,
        )
    except (FileNotFoundError, TypeError, ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"Wrote visual quality-control preview to {written}.")
    return 0


def _run_group_comparison(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        input_path = args.input.resolve()
        sample_output = args.sample_level_output.resolve()
        report_output = args.report_output.resolve()
        if input_path in {sample_output, report_output}:
            raise ValueError("Comparison outputs must not overwrite the input CSV.")
        if sample_output == report_output:
            raise ValueError("Sample-level CSV and JSON report must have different paths.")
        report = compare_groups_from_csv(
            args.input, args.sample_level_output, args.report_output,
            biological_unit_column=args.biological_unit_column,
            group_column=args.group_column,
            measurement_column=args.measurement_column,
            group_a=args.group_a,
            group_b=args.group_b,
            aggregation=args.aggregation,
            method=args.method,
            confidence_level=args.confidence_level,
        )
    except (FileNotFoundError, TypeError, ValueError, OSError) as exc:
        parser.error(str(exc))
    print(
        f"Compared {report['groups'][args.group_a.strip()]['n']} vs "
        f"{report['groups'][args.group_b.strip()]['n']} biological units; "
        f"wrote {args.sample_level_output} and {args.report_output}."
    )
    return 0


def _run_volume_analysis(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        _validate_output_paths(args.volume, args.output, args.metadata_output)
        if args.series_index != 0:
            raise ValueError(
                "The CLI currently calibrates the first TIFF series only; "
                "select the required series into a separate ZYX file before analysis."
            )
        metadata = read_tiff_metadata(args.volume)
        calibration = metadata.to_voxel_calibration()
        labels = load_labeled_volume_tiff(
            args.volume,
            series_index=args.series_index,
            max_uncompressed_bytes=args.max_uncompressed_bytes,
        )
        class_names = _load_class_names(args.class_names)
        measurements = measure_labeled_volume(
            labels,
            calibration,
            background_label=args.background_label,
            label_names=class_names,
            min_component_voxels=args.min_voxels,
        )
        output_path = write_volume_measurements_csv(measurements, args.output)
        metadata_path = write_analysis_metadata(
            input_mask_path=args.volume,
            output_csv_path=output_path,
            calibration=calibration,
            mask_shape=labels.shape,
            foreground=None,
            threshold=None,
            min_area_px=args.min_voxels,
            measurement_count=len(measurements),
            metadata_path=args.metadata_output,
            analysis_type="3D class-wise morphometry of a researcher-annotated ZYX integer label volume",
            label_names=class_names,
            result_count_label="class_count",
            calibration_source="OME-TIFF physical X/Y/Z metadata; verify against acquisition records",
        )
    except (FileNotFoundError, TypeError, ValueError, OSError) as exc:
        parser.error(str(exc))
    print(
        f"Measured {len(measurements)} 3D annotation class(es); "
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
    if args.command == "overlay-labels":
        return _run_overlay_analysis(args, parser)
    if args.command == "compare-groups":
        return _run_group_comparison(args, parser)
    if args.command == "measure-volume":
        return _run_volume_analysis(args, parser)

    parser.error("A command is required.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
