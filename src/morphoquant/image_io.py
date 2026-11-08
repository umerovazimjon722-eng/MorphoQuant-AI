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
