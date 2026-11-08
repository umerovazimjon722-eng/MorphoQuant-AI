"""Strict loading helpers for researcher-prepared binary masks."""

from numbers import Real
from pathlib import Path
from typing import Literal, Union

import numpy as np
from PIL import Image, UnidentifiedImageError

PathLike = Union[str, Path]
Foreground = Literal["bright", "dark"]
_GRAYSCALE_MODES = {"1", "L", "I", "I;16", "I;16B", "I;16L", "F"}


def load_binary_mask(
    path: PathLike,
    *,
    threshold: float | None = None,
    foreground: Foreground = "bright",
) -> np.ndarray:
    """Load a grayscale mask as a 2D Boolean array.

    With no threshold, the image must contain no more than two distinct
    intensity values. The brighter value is foreground by default; use
    foreground="dark" to select the darker value instead.

    For anti-aliased or non-binary grayscale masks, provide an explicit
    threshold. Bright foreground uses pixel > threshold; dark foreground
    uses pixel < threshold. A constant image is treated as an empty mask,
    because foreground cannot be inferred from a single intensity value.

    RGB, palette-indexed, and other non-grayscale images are rejected rather
    than silently converted into masks.
    """
    if foreground not in ("bright", "dark"):
        raise ValueError("foreground must be either 'bright' or 'dark'.")

    image_path = Path(path)
    if not image_path.is_file():
        raise FileNotFoundError(f"Mask file does not exist: {image_path}")

    try:
        with Image.open(image_path) as image:
            if image.mode not in _GRAYSCALE_MODES:
                raise ValueError(
                    f"Expected a grayscale mask; received image mode {image.mode!r}."
                )
            values = np.asarray(image).copy()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"Could not read a supported mask image: {image_path}") from exc

    if values.ndim != 2:
        raise ValueError("Mask image must be two-dimensional grayscale.")
    if not np.issubdtype(values.dtype, np.number) and values.dtype != np.bool_:
        raise TypeError("Mask image must contain numeric grayscale values.")
    if not np.isfinite(values).all():
        raise ValueError("Mask image contains non-finite intensity values.")

    if threshold is None:
        unique_values = np.unique(values)
        if unique_values.size > 2:
            raise ValueError(
                "Mask contains more than two intensity values. "
                "Supply an explicit threshold for grayscale/anti-aliased masks."
            )
        if unique_values.size == 1:
            return np.zeros(values.shape, dtype=bool)
        selected_value = unique_values[-1] if foreground == "bright" else unique_values[0]
        return np.asarray(values == selected_value, dtype=bool)

    if isinstance(threshold, bool) or not isinstance(threshold, Real):
        raise TypeError("threshold must be a finite numeric value or None.")
    if not np.isfinite(threshold):
        raise ValueError("threshold must be finite.")

    if foreground == "bright":
        return np.asarray(values > threshold, dtype=bool)
    return np.asarray(values < threshold, dtype=bool)


def load_labeled_mask(path: PathLike) -> np.ndarray:
    """Load a grayscale integer label image without applying thresholding.

    Integer class IDs are preserved. RGB, palette-indexed, floating-point,
    and negative-valued label images are rejected to avoid silently changing
    annotation identities.
    """
    image_path = Path(path)
    if not image_path.is_file():
        raise FileNotFoundError(f"Label mask file does not exist: {image_path}")

    try:
        with Image.open(image_path) as image:
            if image.mode not in {"1", "L", "I", "I;16", "I;16B", "I;16L"}:
                raise ValueError(
                    f"Expected a grayscale integer label image; received mode {image.mode!r}."
                )
            values = np.asarray(image).copy()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"Could not read a supported label image: {image_path}") from exc

    if values.ndim != 2:
        raise ValueError("Label image must be two-dimensional grayscale.")
    if values.dtype == np.bool_ or not np.issubdtype(values.dtype, np.integer):
        raise TypeError("Label image must contain integer class IDs.")
    if np.any(values < 0):
        raise ValueError("Label IDs must be non-negative.")
    return values
