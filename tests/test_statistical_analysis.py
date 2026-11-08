import numpy as np
import pytest

from morphoquant.statistical_analysis import (
    adjust_pvalues_bh,
    compare_independent_groups,
    describe_samples,
)


def test_describe_samples_returns_summary_statistics():
    result = describe_samples([1, 2, 3, 4])
    assert result["n"] == 4
    assert result["mean"] == pytest.approx(2.5)
    assert result["sd"] == pytest.approx(np.std([1, 2, 3, 4], ddof=1))
    assert result["median"] == pytest.approx(2.5)
    assert result["q1"] == pytest.approx(1.75)
    assert result["q3"] == pytest.approx(3.25)


def test_welch_comparison_returns_mean_difference_and_confidence_interval():
    result = compare_independent_groups(
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        method="welch",
    )
    assert result["method"] == "welch"
    assert result["estimated_mean_difference_a_minus_b"] == pytest.approx(-4.0)
    assert result["p_value"] < 0.05
    assert result["ci_lower_mean_difference"] < -4.0
    assert result["ci_upper_mean_difference"] > -4.0
    assert result["degrees_of_freedom"] > 0


def test_mann_whitney_reports_rank_biserial_correlation():
    result = compare_independent_groups(
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        method="mannwhitney",
    )
    assert result["p_value"] < 0.05
    assert result["rank_biserial_correlation"] == pytest.approx(-1.0)
    assert result["ci_lower_mean_difference"] is None


def test_benjamini_hochberg_preserves_input_order_and_monotonicity():
    adjusted = adjust_pvalues_bh([0.01, 0.04, 0.03])
    assert adjusted == pytest.approx([0.03, 0.04, 0.04])


@pytest.mark.parametrize("values", [[], [1], [1, float("nan")], [1, float("inf")]])
def test_descriptive_statistics_reject_invalid_or_too_small_samples(values):
    with pytest.raises(ValueError):
        describe_samples(values)


def test_group_comparison_rejects_nonfinite_and_invalid_method():
    with pytest.raises(ValueError):
        compare_independent_groups([1, 2], [3, float("nan")])
    with pytest.raises(ValueError):
        compare_independent_groups([1, 2], [3, 4], method="invalid")


@pytest.mark.parametrize("values", [[-0.1], [1.1], [float("nan")]])
def test_bh_rejects_invalid_p_values(values):
    with pytest.raises(ValueError):
        adjust_pvalues_bh(values)


def test_welch_rejects_zero_variance_in_both_groups():
    with pytest.raises(ValueError, match="zero within-group variance"):
        compare_independent_groups([2, 2, 2], [5, 5, 5], method="welch")


def test_aggregate_subsamples_by_biological_unit_prevents_pseudoreplication():
    from morphoquant.statistical_analysis import aggregate_subsamples_by_unit

    records = [
        {"animal_id": "A1", "group": "control", "field_area": 10.0},
        {"animal_id": "A1", "group": "control", "field_area": 12.0},
        {"animal_id": "A2", "group": "control", "field_area": 14.0},
        {"animal_id": "B1", "group": "metabolic", "field_area": 20.0},
        {"animal_id": "B1", "group": "metabolic", "field_area": 22.0},
    ]

    result = aggregate_subsamples_by_unit(
        records,
        biological_unit_key="animal_id",
        measurement_key="field_area",
        group_key="group",
        aggregation="mean",
    )

    assert len(result) == 3
    assert result[0]["animal_id"] == "A1"
    assert result[0]["n_subsamples"] == 2
    assert result[0]["field_area"] == pytest.approx(11.0)
    assert result[0]["group"] == "control"
    assert result[2]["animal_id"] == "B1"
    assert result[2]["field_area"] == pytest.approx(21.0)


def test_aggregate_subsamples_rejects_mixed_groups_within_animal():
    from morphoquant.statistical_analysis import aggregate_subsamples_by_unit

    records = [
        {"animal_id": "A1", "group": "control", "value": 1.0},
        {"animal_id": "A1", "group": "treated", "value": 2.0},
    ]
    with pytest.raises(ValueError, match="multiple groups"):
        aggregate_subsamples_by_unit(
            records,
            biological_unit_key="animal_id",
            measurement_key="value",
            group_key="group",
        )


def test_aggregate_subsamples_rejects_missing_unit_or_nonfinite_measurement():
    from morphoquant.statistical_analysis import aggregate_subsamples_by_unit

    with pytest.raises(ValueError, match="missing biological-unit"):
        aggregate_subsamples_by_unit(
            [{"animal_id": "", "value": 1.0}],
            biological_unit_key="animal_id",
            measurement_key="value",
        )
    with pytest.raises(ValueError, match="finite"):
        aggregate_subsamples_by_unit(
            [{"animal_id": "A1", "value": float("nan")}],
            biological_unit_key="animal_id",
            measurement_key="value",
        )


def test_aggregate_subsamples_supports_median():
    from morphoquant.statistical_analysis import aggregate_subsamples_by_unit

    result = aggregate_subsamples_by_unit(
        [
            {"animal_id": "A1", "value": 2.0},
            {"animal_id": "A1", "value": 6.0},
            {"animal_id": "A1", "value": 100.0},
        ],
        biological_unit_key="animal_id",
        measurement_key="value",
        aggregation="median",
    )
    assert result[0]["value"] == pytest.approx(6.0)
