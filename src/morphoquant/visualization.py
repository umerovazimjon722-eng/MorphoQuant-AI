"""Visual quality-control overlays for researcher-annotated label masks."""

import colorsys
import math
from numbers import Integral, Real
from pathlib import Path
from typing import Mapping, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage.segmentation import find_boundaries

PathLike = Union[str, Path]
_PALETTE = (
    (230, 159, 0), (0, 114, 178), (0, 158, 115), (204, 121, 167),
    (213, 94, 0), (86, 180, 233), (240, 228, 66),
)


def _class_color(index: int) -> tuple[int, int, int]:
    if index < len(_PALETTE):
        return _PALETTE[index]
    hue = (index * 0.618033988749895) % 1.0
    red, green, blue = colorsys.hsv_to_rgb(hue, 0.72, 0.92)
    return round(red * 255), round(green * 255), round(blue * 255)


def save_label_overlay(
    image: np.ndarray,
    label_mask: np.ndarray,
    output_path: PathLike,
    *,
    class_names: Mapping[int, str] | None = None,
    background_label: int = 0,
    alpha: float = 0.35,
    max_dimension: int = 2400,
) -> Path:
    """Save original and annotated images side by side with boundaries and a legend.

    The label mask must be supplied by a researcher; no segmentation or class
    inference is performed. If a preview is downscaled, that preview must not
    be used for quantitative measurements.
    """
    rgb = np.asarray(image)
    labels = np.asarray(label_mask)

    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("image must have shape (rows, columns, 3).")
    if rgb.dtype != np.uint8:
        raise TypeError("image must have uint8 dtype.")
    if labels.ndim != 2:
        raise ValueError("label_mask must be two-dimensional.")
    if labels.dtype == np.bool_ or not np.issubdtype(labels.dtype, np.integer):
        raise TypeError("label_mask must contain integer class IDs.")
    if np.any(labels < 0):
        raise ValueError("label_mask class IDs must be non-negative.")
    if rgb.shape[:2] != labels.shape:
        raise ValueError("image and label_mask must have identical height and width.")
    if isinstance(background_label, bool) or not isinstance(background_label, Integral):
        raise TypeError("background_label must be an integer.")
    if isinstance(alpha, bool) or not isinstance(alpha, Real):
        raise TypeError("alpha must be a real number between 0 and 1.")
    if not math.isfinite(float(alpha)) or not 0 <= float(alpha) <= 1:
        raise ValueError("alpha must be finite and between 0 and 1.")
    if isinstance(max_dimension, bool) or not isinstance(max_dimension, Integral):
        raise TypeError("max_dimension must be a positive integer.")
    if max_dimension < 1:
        raise ValueError("max_dimension must be a positive integer.")
    if class_names is not None:
        if not isinstance(class_names, Mapping):
            raise TypeError("class_names must be a mapping from integer IDs to names.")
        for class_id, name in class_names.items():
            if isinstance(class_id, bool) or not isinstance(class_id, Integral):
                raise TypeError("class_names keys must be integer label IDs.")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("class_names values must be non-empty strings.")

    destination = Path(output_path)
    if destination.suffix.lower() != ".png":
        raise ValueError("output_path must have a .png extension for lossless QC output.")

    class_ids = [
        int(value) for value in np.unique(labels)
        if int(value) != int(background_label)
    ]
    class_colors = {class_id: _class_color(i) for i, class_id in enumerate(class_ids)}

    overlay = rgb.astype(np.float32, copy=True)
    opacity = float(alpha)
    for class_id, color in class_colors.items():
        selected = labels == class_id
        overlay[selected] = (
            (1.0 - opacity) * overlay[selected]
            + opacity * np.asarray(color, dtype=np.float32)
        )
    if class_ids:
        boundaries = find_boundaries(
            labels, mode="thick", background=int(background_label)
        )
        overlay[boundaries] = (20, 20, 20)
    overlay_rgb = np.clip(np.rint(overlay), 0, 255).astype(np.uint8)

    height, width = labels.shape
    scale = min(1.0, float(max_dimension) / max(height, width))
    panel_size = (
        max(1, round(width * scale)),
        max(1, round(height * scale)),
    )
    original_panel = Image.fromarray(rgb, mode="RGB")
    overlay_panel = Image.fromarray(overlay_rgb, mode="RGB")
    if scale < 1:
        original_panel = original_panel.resize(panel_size, Image.Resampling.LANCZOS)
        overlay_panel = overlay_panel.resize(panel_size, Image.Resampling.NEAREST)

    margin, gap, header = 20, 20, 32
    row_height = 24
    legend_rows = max(1, len(class_ids))
    legend_height = legend_rows * row_height + 12
    canvas_width = margin * 2 + panel_size[0] * 2 + gap
    canvas_height = margin + header + panel_size[1] + 14 + legend_height + margin
    canvas = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    left_x = margin
    right_x = margin + panel_size[0] + gap
    image_y = margin + header

    draw.text((left_x, margin), "Original image", fill=(25, 25, 25), font=font)
    draw.text((right_x, margin), "Researcher-annotated overlay", fill=(25, 25, 25), font=font)
    canvas.paste(original_panel, (left_x, image_y))
    canvas.paste(overlay_panel, (right_x, image_y))

    legend_y = image_y + panel_size[1] + 14
    if not class_ids:
        draw.text((margin, legend_y), "No non-background labels found.", fill=(40, 40, 40), font=font)
    else:
        total_foreground = int(np.count_nonzero(labels != int(background_label)))
        for index, class_id in enumerate(class_ids):
            y = legend_y + index * row_height
            color = class_colors[class_id]
            draw.rectangle(
                (margin, y + 3, margin + 13, y + 16),
                fill=color, outline=(30, 30, 30),
            )
            count = int(np.count_nonzero(labels == class_id))
            percent = 100.0 * count / total_foreground if total_foreground else 0.0
            name = (
                class_names[class_id].strip()
                if class_names is not None and class_id in class_names
                else f"class {class_id}"
            )
            draw.text(
                (margin + 22, y + 2),
                f"{name} (ID {class_id}): {count:,} px ({percent:.1f}% foreground)",
                fill=(30, 30, 30), font=font,
            )
    if scale < 1:
        draw.text(
            (margin, canvas_height - margin - 10),
            f"Preview downscaled to {panel_size[0]} x {panel_size[1]}; quantify using original arrays.",
            fill=(95, 95, 95), font=font,
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    try:
        with temporary.open("wb") as output:
            canvas.save(output, format="PNG", optimize=True)
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return destination.resolve()
