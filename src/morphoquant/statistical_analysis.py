"""Transparent statistical summaries and independent-group comparisons.

The functions expect independent biological-replicate-level observations.
Do not pass multiple microscope fields from the same animal as if they were
independent animals; aggregate within the experimental unit first or use an
appropriate hierarchical/mixed-effects model.
"""

from typing import Dict, Iterable, List, Literal

import numpy as np
from scipy import stats

ComparisonMethod = Literal["welch", "mannwhitney"]


def _validated_sample(values: Iterable[float], name: str) -> np.ndarray:
    try:
        sample = np.asarray(list(values), dtype=float)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be an iterable of numeric values.") from exc

    if sample.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional.")
    if sample.size < 2:
        raise ValueError(f"{name} must contain at least two independent observations.")
    if not np.isfinite(sample).all():
        raise ValueError(f"{name} must contain only finite values.")
    return sample


def describe_samples(values: Iterable[float]) -> Dict[str, float | int | None]:
    """Return descriptive statistics for independent sample-level values."""
    sample = _validated_sample(values, "values")
    q1, median, q3 = np.quantile(sample, [0.25, 0.5, 0.75])
    return {
        "n": int(sample.size),
        "mean": float(np.mean(sample)),
        "sd": float(np.std(sample, ddof=1)),
        "median": float(median),
        "q1": float(q1),
        "q3": float(q3),
        "minimum": float(np.min(sample)),
        "maximum": float(np.max(sample)),
    }


def compare_independent_groups(
    group_a: Iterable[float],
    group_b: Iterable[float],
    *,
    method: ComparisonMethod = "welch",
    confidence_level: float = 0.95,
) -> Dict[str, float | int | str | None]:
    """Compare two independent groups using Welch's t-test or Mann–Whitney U.

    Welch's test returns a two-sided p-value and a Welch-Satterthwaite
    confidence interval for the difference in means (group A minus group B).
    Mann–Whitney returns a two-sided p-value and rank-biserial correlation;
    it does not return a confidence interval for the median difference.

    Selection of a test must be justified by the research design and data
    characteristics. This function does not automatically test assumptions,
    model repeated measures, adjust for covariates, or correct for multiple
    outcomes. Use one independent observation per biological experimental
    unit unless a hierarchical model is used.
    """
    a = _validated_sample(group_a, "group_a")
    b = _validated_sample(group_b, "group_b")

    if method not in ("welch", "mannwhitney"):
        raise ValueError("method must be 'welch' or 'mannwhitney'.")
    if not isinstance(confidence_level, (int, float)) or isinstance(confidence_level, bool):
        raise TypeError("confidence_level must be a real number.")
    if not 0 < float(confidence_level) < 1:
        raise ValueError("confidence_level must be strictly between 0 and 1.")

    mean_a = float(np.mean(a))
    mean_b = float(np.mean(b))
    difference = mean_a - mean_b
    result: Dict[str, float | int | str | None] = {
        "method": method,
        "n_a": int(a.size),
        "n_b": int(b.size),
        "mean_a": mean_a,
        "mean_b": mean_b,
        "mean_difference_a_minus_b": difference,
        "median_a": float(np.median(a)),
        "median_b": float(np.median(b)),
        "statistic": None,
        "degrees_of_freedom": None,
        "p_value": None,
        "confidence_level": float(confidence_level),
        "ci_lower_mean_difference": None,
        "ci_upper_mean_difference": None,
        "rank_biserial_correlation": None,
    }

    if method == "welch":
        test = stats.ttest_ind(a, b, equal_var=False, alternative="two-sided")
        var_a = float(np.var(a, ddof=1))
        var_b = float(np.var(b, ddof=1))
        term_a = var_a / a.size
        term_b = var_b / b.size
        standard_error_squared = term_a + term_b
        denominator = (term_a**2 / (a.size - 1)) + (term_b**2 / (b.size - 1))
        degrees_freedom = standard_error_squared**2 / denominator
        critical_value = float(
            stats.t.ppf((1.0 + float(confidence_level)) / 2.0, degrees_freedom)
        )
        margin = critical_value * float(np.sqrt(standard_error_squared))

        result.update(
            {
                "statistic": float(test.statistic),
                "degrees_of_freedom": float(degrees_freedom),
                "p_value": float(test.pvalue),
                "ci_lower_mean_difference": float(difference - margin),
                "ci_upper_mean_difference": float(difference + margin),
            }
        )
        return result

    test = stats.mannwhitneyu(a, b, alternative="two-sided", method="auto")
    rank_biserial = (2.0 * float(test.statistic) / (a.size * b.size)) - 1.0
    result.update(
        {
            "statistic": float(test.statistic),
            "p_value": float(test.pvalue),
            "rank_biserial_correlation": float(rank_biserial),
        }
    )
    return result


def adjust_pvalues_bh(p_values: Iterable[float]) -> List[float]:
    """Adjust a family of p-values using Benjamini–Hochberg FDR control."""
    try:
        values = np.asarray(list(p_values), dtype=float)
    except (TypeError, ValueError) as exc:
        raise TypeError("p_values must be an iterable of numeric values.") from exc

    if values.ndim != 1:
        raise ValueError("p_values must be one-dimensional.")
    if values.size == 0:
        return []
    if not np.isfinite(values).all() or np.any((values < 0) | (values > 1)):
        raise ValueError("p_values must be finite and between 0 and 1.")

    order = np.argsort(values)
    ranked = values[order]
    count = ranked.size
    adjusted_sorted = ranked * count / np.arange(1, count + 1)
    adjusted_sorted = np.minimum.accumulate(adjusted_sorted[::-1])[::-1]
    adjusted_sorted = np.clip(adjusted_sorted, 0.0, 1.0)

    adjusted = np.empty_like(adjusted_sorted)
    adjusted[order] = adjusted_sorted
    return [float(value) for value in adjusted]
