# Statistical methods and interpretation

## Experimental unit and independence

The current two-group functions are intended for **independent biological experimental units**. In an animal experiment, that is usually the animal; in a human study, it may be the participant or another prespecified independent unit.

Multiple images, sections, microscopic fields, cells, or nuclei from the same biological sample are generally nested technical/subsample observations. They must not be treated as independent biological replicates. Either:
- calculate a prespecified sample-level summary before group comparison; or
- use a hierarchical/mixed-effects model that represents the nesting structure.

The current module does not fit mixed-effects models, repeated-measures models, covariate-adjusted models, survival models, or generalized linear models.

## Descriptive statistics

`describe_samples` returns sample size, arithmetic mean, sample standard deviation, median, first and third quartiles, minimum, and maximum. These summaries do not replace plots or distribution inspection.

## Welch's independent-samples t-test

`compare_independent_groups(..., method="welch")` performs a two-sided Welch t-test. It does not assume equal population variances. The reported confidence interval uses the Welch–Satterthwaite degrees of freedom and estimates the difference in arithmetic means (group A minus group B).

Welch's test still relies on independent observations and is most reliable when the sampling distribution of the mean is adequately behaved. Inspect the data, outliers, design, and sample size before interpreting the p-value.

## Mann–Whitney U test

`compare_independent_groups(..., method="mannwhitney")` performs a two-sided Mann–Whitney U test and reports rank-biserial correlation. It is a rank-based comparison; it is **not automatically a test of medians** unless additional distribution-shape assumptions are defensible. The function therefore does not label the median difference as the test estimate or provide a median-difference confidence interval.

## Multiple outcomes

`adjust_pvalues_bh` applies the Benjamini–Hochberg false-discovery-rate adjustment to a supplied family of p-values. The researcher must define the family of hypotheses before analysis and report both raw and adjusted p-values. FDR adjustment does not correct a poorly specified design or inappropriate test selection.

## Reporting

At minimum, report the experimental unit, group sample sizes, summary statistics, selected test and rationale, test statistic, degrees of freedom where applicable, raw p-value, adjusted p-value when used, effect estimate and confidence interval where available, and relevant limitations.

Do not interpret statistical significance as biological importance. Consider effect magnitude, uncertainty, study design, prior evidence, and measurement validity. The software does not automatically select the statistically appropriate test for a particular experiment.


## Aggregating fields and sections within the experimental unit

The helper `aggregate_subsamples_by_unit` accepts row dictionaries in which each row represents a field, section, or other subsample. It groups those rows by a biological-unit identifier (for example, animal ID) and returns one summary value per biological unit. An optional group key is checked for consistency so that a single animal cannot silently be assigned to two experimental groups.

Choose mean or median aggregation before inspecting group differences and justify that choice in the protocol. This simple aggregation is suitable only when a sample-level summary matches the scientific estimand. It does not model within-animal variation; use an appropriate mixed-effects or hierarchical model when that variation is itself scientifically important.

After aggregation, the number of returned rows is the number of biological units, not the number of image fields. Keep the original subsample data and document the aggregation rule.


## End-to-end CSV group comparison

The `compare-groups` command expects a tidy CSV with one row per field, section, or other subsample and explicit columns for biological-unit ID, experimental group, and one numeric measurement. Rows are aggregated by biological-unit ID before group-level statistics are calculated.

Only the two group labels named by the researcher are compared. Other groups are excluded from that specific comparison and listed in the JSON report. The tool writes a sample-level CSV with one row per biological unit and a JSON report containing summaries, test output, input and output checksums, settings, and interpretive limitations.

Use this command only when the chosen sample-level mean or median represents the scientific estimand. If within-animal variation is important, a simple aggregation is insufficient; use an appropriate mixed-effects or hierarchical model. The current CLI supports Welch's t-test and Mann–Whitney U for two independent groups and does not automatically check assumptions or adjust for multiple outcomes.
