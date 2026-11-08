"""MorphoQuant AI: reproducible quantitative histology utilities."""

from .calibration import MicroscopeCalibration
from .csv_export import write_labeled_measurements_csv, write_measurements_csv
from .masks import load_binary_mask, load_labeled_mask
from .morphometry import measure_binary_mask
from .labeled_morphometry import measure_labeled_mask
from .statistical_analysis import adjust_pvalues_bh, compare_independent_groups, describe_samples
from .tiff_metadata import TiffImageMetadata, read_tiff_metadata

__all__ = [
    "MicroscopeCalibration",
    "load_binary_mask",
    "load_labeled_mask",
    "measure_binary_mask",
    "measure_labeled_mask",
    "write_measurements_csv",
    "write_labeled_measurements_csv",
    "describe_samples",
    "compare_independent_groups",
    "adjust_pvalues_bh",
    "TiffImageMetadata",
    "read_tiff_metadata",
]
__version__ = "0.1.0"
