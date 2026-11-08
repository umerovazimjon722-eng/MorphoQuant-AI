"""Agreement metrics for comparing independently produced label masks.

These metrics evaluate annotation or segmentation agreement. They do not
establish anatomical correctness, clinical validity, or biological truth.
"""

from numbers import Integral, Real
from typing import Dict, List, Mapping, Sequence

import numpy as np
from scipy import ndimage


def _validate_label_array(array: np.ndarray, name: str) -> np.ndarray:
    values = np.asarray(array)
    if values.ndim not in (2, 3):
        raise ValueError(f"{name} must be a 2D or 3D label array.")
    if values.dtype == np.bool_ or not np.issubdtype(values.dtype, np.integer):
        raise TypeError(f"{name} must contain integer class labels.")
    if np.any(values < 0):
        raise ValueError(f"{name} class labels must be non-negative.")
    return values


def _validate_spacing(spacing_um: Sequence[float], ndim: int) -> tuple[float, ...]:
    if isinstance(spacing_um, (str, bytes)):
        raise TypeError("spacing_um must be a sequence of physical axis spacings.")
    try:
        spacing = tuple(spacing_um)
    except TypeError as exc:
        raise TypeError("spacing_um must be a sequence of physical axis spacings.") from exc
    if len(spacing) != ndim:
        raise ValueError(f"spacing_um must contain {ndim} values in array-axis order.")
    converted = []
    for axis, value in enumerate(spacing):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"spacing_um[{axis}] must be a real number.")
        numeric = float(value)
        if not np.isfinite(numeric) or numeric <= 0:
            raise ValueError(f"spacing_um[{axis}] must be finite and greater than zero.")
        converted.append(numeric)
    return tuple(converted)


def _surface(mask: np.ndarray) -> np.ndarray:
    """Extract a one-voxel object surface with background outside the image."""
    structure = ndimage.generate_binary_structure(mask.ndim, 1)
    eroded = ndimage.binary_erosion(
        mask,
        structure=structure,
        border_value=0,
    )
    return mask & ~eroded


def compare_label_masks(
    reference: np.ndarray,
    comparison: np.ndarray,
    *,
    spacing_um: Sequence[float],
    background_label: int = 0,
    label_names: Mapping[int, str] | None = None,
) -> List[Dict[str, float | int | str | None]]:
    """Compare two 2D or 3D integer label masks class by class.

    reference is the adjudicated/reference annotation; comparison is the
    second annotator or algorithm output. Both arrays must be aligned,
    have identical shape and use the same class-ID convention. spacing_um
    follows NumPy array-axis order: (y, x) for 2D or (z, y, x) for 3D.

    Per class, results include confusion counts, Dice, intersection-over-
    union, precision, recall, specificity, symmetric average surface
    distance, Hausdorff distance, and 95th-percentile Hausdorff distance.
    Surface distances are reported in micrometres.

    Empty-class convention:
    - If both masks omit a class, Dice and IoU are 1.0 (agreement on absence).
    - Precision or recall is None if its denominator is zero.
    - Surface distances are None when either mask has no foreground voxels.

    The function does not infer which mask is biologically correct. For
    independent annotators, define an adjudication protocol and state which
    annotation is used as the reference.
    """
    ref = _validate_label_array(reference, "reference")
    pred = _validate_label_array(comparison, "comparison")
    if ref.shape != pred.shape:
        raise ValueError("reference and comparison must have identical shapes.")
    spacing = _validate_spacing(spacing_um, ref.ndim)

    if isinstance(background_label, bool) or not isinstance(background_label, Integral):
        raise TypeError("background_label must be an integer.")
    if label_names is not None:
        if not isinstance(label_names, Mapping):
            raise TypeError("label_names must map integer class IDs to names.")
        for class_id, name in label_names.items():
            if isinstance(class_id, bool) or not isinstance(class_id, Integral):
                raise TypeError("label_names keys must be integer class IDs.")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("label_names values must be non-empty strings.")

    class_ids = sorted(
        (set(int(x) for x in np.unique(ref)) | set(int(x) for x in np.unique(pred)))
        - {int(background_label)}
    )
    total = int(ref.size)
    results: List[Dict[str, float | int | str | None]] = []

    for class_id in class_ids:
        reference_class = ref == class_id
        comparison_class = pred == class_id
        tp = int(np.count_nonzero(reference_class & comparison_class))
        fp = int(np.count_nonzero(~reference_class & comparison_class))
        fn = int(np.count_nonzero(reference_class & ~comparison_class))
        tn = total - tp - fp - fn
        reference_count = tp + fn
        comparison_count = tp + fp
        overlap_denominator = 2 * tp + fp + fn
        union_count = tp + fp + fn

        dice = (2.0 * tp / overlap_denominator) if overlap_denominator else 1.0
        iou = (tp / union_count) if union_count else 1.0
        precision = (tp / comparison_count) if comparison_count else None
        recall = (tp / reference_count) if reference_count else None
        specificity = (tn / (tn + fp)) if (tn + fp) else None

        assd = None
        hausdorff = None
        hausdorff_95 = None
        if reference_count and comparison_count:
            reference_surface = _surface(reference_class)
            comparison_surface = _surface(comparison_class)
            distance_to_comparison = ndimage.distance_transform_edt(
                ~comparison_surface, sampling=spacing
            )
            distance_to_reference = ndimage.distance_transform_edt(
                ~reference_surface, sampling=spacing
            )
            ref_to_pred = distance_to_comparison[reference_surface]
            pred_to_ref = distance_to_reference[comparison_surface]
            combined_distances = np.concatenate((ref_to_pred, pred_to_ref))
            assd = float((np.mean(ref_to_pred) + np.mean(pred_to_ref)) / 2.0)
            hausdorff = float(max(np.max(ref_to_pred), np.max(pred_to_ref)))
            hausdorff_95 = float(np.percentile(combined_distances, 95))

        class_name = (
            str(label_names[class_id]).strip()
            if label_names is not None and class_id in label_names
            else str(class_id)
        )
        results.append(
            {
                "class_id": int(class_id),
                "class_name": class_name,
                "reference_pixels_or_voxels": reference_count,
                "comparison_pixels_or_voxels": comparison_count,
                "true_positive": tp,
                "false_positive": fp,
                "false_negative": fn,
                "true_negative": tn,
                "dice": float(dice),
                "intersection_over_union": float(iou),
                "precision": None if precision is None else float(precision),
                "recall": None if recall is None else float(recall),
                "specificity": None if specificity is None else float(specificity),
                "assd_um": assd,
                "hausdorff_distance_um": hausdorff,
                "hausdorff_95_distance_um": hausdorff_95,
            }
        )

    return results
