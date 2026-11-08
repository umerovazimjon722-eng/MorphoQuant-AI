import numpy as np
import pytest

from morphoquant.agreement import compare_label_masks


def test_identical_2d_masks_have_perfect_overlap_and_zero_surface_distance():
    mask = np.zeros((12, 12), dtype=np.uint8)
    mask[2:8, 3:9] = 1
    result = compare_label_masks(
        mask, mask.copy(), spacing_um=(0.5, 0.25),
        label_names={1: "cortex"},
    )[0]
    assert result["class_name"] == "cortex"
    assert result["dice"] == pytest.approx(1.0)
    assert result["intersection_over_union"] == pytest.approx(1.0)
    assert result["assd_um"] == pytest.approx(0.0)
    assert result["hausdorff_distance_um"] == pytest.approx(0.0)
    assert result["hausdorff_95_distance_um"] == pytest.approx(0.0)


def test_shifted_masks_report_nonzero_physical_boundary_distance():
    reference = np.zeros((10, 10), dtype=np.uint8)
    comparison = np.zeros_like(reference)
    reference[2:5, 2:5] = 1
    comparison[2:5, 3:6] = 1
    result = compare_label_masks(
        reference, comparison, spacing_um=(1.0, 2.0)
    )[0]
    assert 0 < result["dice"] < 1
    assert 0 < result["intersection_over_union"] < 1
    assert result["hausdorff_distance_um"] == pytest.approx(2.0)
    assert result["assd_um"] > 0


def test_3d_surface_distances_respect_anisotropic_voxel_spacing():
    reference = np.zeros((8, 8, 8), dtype=np.uint8)
    comparison = np.zeros_like(reference)
    reference[2:5, 2:5, 2:5] = 1
    comparison[3:6, 2:5, 2:5] = 1
    result = compare_label_masks(
        reference, comparison, spacing_um=(3.0, 1.0, 0.5)
    )[0]
    assert result["hausdorff_distance_um"] == pytest.approx(3.0)


def test_missing_class_is_reported_with_zero_overlap_and_null_surface_distances():
    reference = np.zeros((5, 5), dtype=np.uint8)
    comparison = np.zeros_like(reference)
    reference[1:3, 1:3] = 1
    result = compare_label_masks(reference, comparison, spacing_um=(1.0, 1.0))[0]
    assert result["dice"] == 0.0
    assert result["intersection_over_union"] == 0.0
    assert result["recall"] == 0.0
    assert result["precision"] is None
    assert result["assd_um"] is None
    assert result["hausdorff_distance_um"] is None


def test_label_masks_with_different_class_ids_are_compared_separately():
    reference = np.zeros((6, 6), dtype=np.uint8)
    comparison = np.zeros_like(reference)
    reference[1:4, 1:4] = 1
    comparison[1:4, 1:4] = 2
    results = compare_label_masks(reference, comparison, spacing_um=(1.0, 1.0))
    by_id = {row["class_id"]: row for row in results}
    assert by_id[1]["dice"] == 0.0
    assert by_id[2]["dice"] == 0.0


@pytest.mark.parametrize(
    "reference,comparison,spacing",
    [
        (np.zeros((3, 3)), np.zeros((3, 3)), (1.0, 1.0)),
        (np.zeros((3, 3), dtype=bool), np.zeros((3, 3), dtype=bool), (1.0, 1.0)),
        (-np.ones((3, 3), dtype=int), -np.ones((3, 3), dtype=int), (1.0, 1.0)),
        (np.zeros((3, 3), dtype=int), np.zeros((3, 4), dtype=int), (1.0, 1.0)),
        (np.zeros((3, 3), dtype=int), np.zeros((3, 3), dtype=int), (1.0,)),
        (np.zeros((3, 3, 3), dtype=int), np.zeros((3, 3, 3), dtype=int), (1.0, 0.0, 1.0)),
    ],
)
def test_agreement_rejects_invalid_inputs(reference, comparison, spacing):
    with pytest.raises((TypeError, ValueError)):
        compare_label_masks(reference, comparison, spacing_um=spacing)


def test_agreement_rejects_invalid_label_names():
    labels = np.zeros((5, 5), dtype=np.uint8)
    labels[1:3, 1:3] = 1
    with pytest.raises(ValueError):
        compare_label_masks(
            labels, labels, spacing_um=(1.0, 1.0), label_names={1: ""}
        )


def test_agreement_reports_explicitly_named_class_absent_from_both_masks():
    reference = np.zeros((8, 8), dtype=np.uint8)
    comparison = np.zeros_like(reference)
    result = compare_label_masks(
        reference,
        comparison,
        spacing_um=(0.5, 0.25),
        label_names={1: "cortex"},
    )[0]
    assert result["class_id"] == 1
    assert result["class_name"] == "cortex"
    assert result["reference_pixels_or_voxels"] == 0
    assert result["comparison_pixels_or_voxels"] == 0
    assert result["dice"] == 1.0
    assert result["intersection_over_union"] == 1.0
    assert result["precision"] is None
    assert result["recall"] is None
    assert result["assd_um"] is None
