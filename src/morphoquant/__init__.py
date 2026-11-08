"""MorphoQuant AI: reproducible quantitative histology utilities."""

from .calibration import MicroscopeCalibration, VoxelCalibration
from .csv_export import write_labeled_measurements_csv, write_measurements_csv
from .masks import load_binary_mask, load_labeled_mask
from .morphometry import measure_binary_mask
from .labeled_morphometry import measure_labeled_mask
from .statistical_analysis import (
    adjust_pvalues_bh,
    aggregate_subsamples_by_unit,
    compare_independent_groups,
    describe_samples,
)
from .tiff_metadata import TiffImageMetadata, read_tiff_metadata
from .study_analysis import compare_groups_from_csv
from .visualization import save_label_overlay
from .agreement import compare_label_masks
from .volume_morphometry import measure_labeled_volume

__all__ = [
    "MicroscopeCalibration",
    "VoxelCalibration",
    "load_binary_mask",
    "load_labeled_mask",
    "measure_binary_mask",
    "measure_labeled_mask",
    "write_measurements_csv",
    "write_labeled_measurements_csv",
    "describe_samples",
    "aggregate_subsamples_by_unit",
    "compare_independent_groups",
    "adjust_pvalues_bh",
    "TiffImageMetadata",
    "read_tiff_metadata",
    "save_label_overlay",
    "compare_groups_from_csv",
    "compare_label_masks",
    "measure_labeled_volume",
]
__version__ = "0.1.0"
