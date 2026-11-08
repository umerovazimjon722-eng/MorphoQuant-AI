"""Small, explicit helpers for reading microscopy image files."""

from pathlib import Path
from typing import Union

import numpy as np
from PIL import Image, UnidentifiedImageError

PathLike = Union[str, Path]


def load_rgb_image(path: PathLike) -> np.ndarray:
    """Load an image as an RGB uint8 array.

    The source file is not modified. Conversion to RGB is performed in memory.
    Pixel calibration is deliberately not inferred by this function.
    """
    image_path = Path(path)
    if not image_path.is_file():
        raise FileNotFoundError(f"Image file does not exist: {image_path}")

    try:
        with Image.open(image_path) as image:
            return np.asarray(image.convert("RGB"), dtype=np.uint8).copy()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"Could not read a supported image file: {image_path}") from exc


def load_labeled_volume_tiff(
    path: PathLike,
    *,
    series_index: int = 0,
    max_uncompressed_bytes: int = 1_000_000_000,
) -> np.ndarray:
    """Load a 3D Z-Y-X integer label volume from one TIFF/OME-TIFF series.

    The selected series must have axes exactly ZYX. Channel, time, RGB, and
    ambiguous axis layouts are rejected. A memory limit is checked before
    decoding. The returned array is an independent copy owned by the caller.

    This function does not register serial sections, interpolate missing
    sections, or infer class identities.
    """
    import math
    import tifffile

    image_path = Path(path)
    if not image_path.is_file():
        raise FileNotFoundError(f"TIFF volume does not exist: {image_path}")
    if isinstance(series_index, bool) or not isinstance(series_index, int):
        raise TypeError("series_index must be an integer.")
    if isinstance(max_uncompressed_bytes, bool) or not isinstance(max_uncompressed_bytes, int):
        raise TypeError("max_uncompressed_bytes must be an integer.")
    if max_uncompressed_bytes < 1:
        raise ValueError("max_uncompressed_bytes must be positive.")

    try:
        with tifffile.TiffFile(image_path) as tiff:
            if series_index < 0 or series_index >= len(tiff.series):
                raise ValueError("series_index is outside the available TIFF series range.")
            series = tiff.series[series_index]
            if str(series.axes) != "ZYX":
                raise ValueError(
                    f"3D label volume requires TIFF axes='ZYX'; found {series.axes!r}."
                )
            shape = tuple(int(value) for value in series.shape)
            estimated_bytes = math.prod(shape) * np.dtype(series.dtype).itemsize
            if estimated_bytes > max_uncompressed_bytes:
                raise ValueError(
                    f"Uncompressed volume requires about {estimated_bytes:,} bytes, "
                    f"exceeding the configured limit of {max_uncompressed_bytes:,} bytes."
                )
            values = series.asarray()
    except (tifffile.TiffFileError, OSError) as exc:
        raise ValueError(f"Could not decode TIFF label volume: {image_path}") from exc

    volume = np.asarray(values)
    if volume.ndim != 3:
        raise ValueError("Decoded label volume is not three-dimensional.")
    if volume.dtype == np.bool_ or not np.issubdtype(volume.dtype, np.integer):
        raise TypeError("TIFF label volume must contain integer class IDs.")
    if np.any(volume < 0):
        raise ValueError("TIFF label class IDs must be non-negative.")
    return volume.copy()
