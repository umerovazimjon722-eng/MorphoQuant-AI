"""Command-line interface for reproducible mask-based morphometry."""

import argparse
from pathlib import Path
from typing import Sequence

from . import __version__
from .calibration import MicroscopeCalibration
from .csv_export import write_measurements_csv
from .masks import load_binary_mask
from .morphometry import measure_binary_mask
from .provenance import write_analysis_metadata


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="morphoquant",
        description=(
            "Measure researcher-prepared grayscale binary masks. "
            "This command does not perform tissue segmentation or diagnosis."
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
    measure.add_argument("mask", type=Path, help="path to a grayscale mask image")
    measure.add_argument(
        "--micrometers-per-pixel",
        type=float,
        default=None,
        help="isotropic pixel size in micrometres per pixel",
    )
    measure.add_argument(
        "--micrometers-per-pixel-x",
        type=float,
        default=None,
        help="horizontal pixel size in micrometres per pixel (use with --micrometers-per-pixel-y)",
    )
    measure.add_argument(
        "--micrometers-per-pixel-y",
        type=float,
        default=None,
        help="vertical pixel size in micrometres per pixel (use with --micrometers-per-pixel-x)",
    )
    measure.add_argument(
        "--output",
        type=Path,
        required=True,
        help="destination CSV file for measurements",
    )
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI. argv is injectable for tests."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "measure-mask":
        try:
            input_path = args.mask.resolve()
            output_path_requested = args.output.resolve()
            metadata_path_requested = (
                args.metadata_output.resolve() if args.metadata_output is not None else None
            )
            if input_path == output_path_requested:
                raise ValueError("The output CSV path must not overwrite the input mask.")
            if metadata_path_requested is not None and metadata_path_requested in {
                input_path,
                output_path_requested,
            }:
                raise ValueError("The metadata JSON path must differ from the input mask and output CSV.")

            calibration = MicroscopeCalibration(
                micrometers_per_pixel=args.micrometers_per_pixel,
                micrometers_per_pixel_x=args.micrometers_per_pixel_x,
                micrometers_per_pixel_y=args.micrometers_per_pixel_y,
            )
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
            )
        except (FileNotFoundError, TypeError, ValueError, OSError) as exc:
            parser.error(str(exc))

        print(
            f"Measured {len(measurements)} connected component(s); "
            f"wrote {output_path} and provenance {metadata_path}."
        )
        return 0

    parser.error("A command is required.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
