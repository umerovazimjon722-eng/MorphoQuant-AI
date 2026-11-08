# Research validation plan

## Purpose

This document defines a proposed validation framework for quantitative histological analysis. It is a protocol-planning aid, not evidence that the current software has been validated on biological tissue.

The initial application is morphometric assessment of adrenal gland tissue in experimental metabolic syndrome. Validation must be specific to the tissue, stain, specimen preparation, imaging system, and intended measurement.

## 1. Define the biological experimental unit

Before collecting images or running statistics, specify:

- species, strain, sex, age, and relevant biological characteristics;
- experimental groups, allocation, intervention, and controls;
- the biological experimental unit (for example, the animal);
- number of biological replicates per group;
- sections per specimen and fields per section;
- primary and secondary morphometric outcomes;
- inclusion, exclusion, and missing-data rules.

Sections, fields of view, cells, nuclei, and segmented objects from the same specimen are usually nested observations, not additional independent biological replicates. Aggregate them using a prespecified rule or analyse them with a suitable hierarchical/mixed-effects model.

## 2. Calibration validation

1. Calibrate each imaging configuration using a stage micrometer, certified scale, or documented acquisition metadata.
2. Record horizontal and vertical pixel spacing separately when the imaging system is anisotropic.
3. Record objective, camera/scanner, resolution, image dimensions, bit depth, file format, and any resampling.
4. Recheck calibration after changing objective, camera, scan resolution, image export, or resampling settings.
5. Keep the calibration image or acquisition record and link it to the analyzed image.

Do not infer micrometres per pixel from nominal magnification or image dimensions alone.

## 3. Annotation and segmentation reference standard

If an automated or semi-automated segmentation module is introduced:

- prepare an annotation manual defining the target structures and exclusion rules;
- use at least two qualified annotators where feasible;
- blind annotators to experimental group when appropriate;
- adjudicate disagreements using a documented process;
- split data by biological specimen, not by image tile, to avoid leakage between training and test sets;
- keep a locked, held-out validation set;
- report class imbalance and the number of specimens, sections, images, and annotated regions.

The current prototype does not segment tissue. It measures masks supplied by the researcher.

## 4. Segmentation performance metrics

Select metrics based on the scientific target and report them per specimen or image as appropriate:

- Dice similarity coefficient;
- intersection over union (Jaccard index);
- boundary distance, such as average symmetric surface distance;
- Hausdorff distance or a robust percentile Hausdorff distance;
- object-level precision, recall, and F1 where separate objects are being detected.

Do not rely on a single overlap metric. A high pixel-overlap score may conceal errors in small structures, boundaries, or biologically important regions.

## 5. Measurement agreement and repeatability

Compare software-derived measurements with expert-reviewed reference measurements.

Recommended analyses include:

- mean bias and limits of agreement using Bland–Altman methods;
- intraclass correlation coefficient (ICC) with the model, unit, and agreement/consistency definition explicitly stated;
- within-observer and between-observer repeatability;
- coefficient of variation or repeatability coefficient where suitable;
- confidence intervals for agreement estimates.

Correlation alone is not a measure of agreement. A high correlation can coexist with systematic measurement bias.

## 6. Statistical analysis

- Prespecify the primary endpoint and comparison before examining group results.
- Report the number of biological replicates separately from the number of sections, fields, and objects.
- Inspect distributions, outliers, missingness, and model assumptions.
- Use Welch's test only when an independent-group mean comparison is scientifically appropriate.
- Use rank-based tests with awareness of what they test; Mann–Whitney is not automatically a test of medians.
- Use hierarchical or mixed-effects methods when measurements are nested or repeated.
- Define the family of hypotheses before applying multiple-testing correction.
- Report effect estimates, uncertainty intervals, raw p-values, and adjusted p-values where appropriate.

The package's current two-group statistical functions do not implement mixed-effects models or automatic assumption checking.

## 7. Data integrity and provenance

For every analysis, preserve:

- immutable source image and checksum;
- mask and checksum;
- calibration source and axis-specific pixel spacing;
- software version and commit;
- image-processing and threshold parameters;
- ROI and exclusion decisions;
- output CSV and provenance JSON;
- analyst and reviewer roles, using coded identifiers where needed.

Do not publish identifiable patient data, confidential laboratory records, or animal/human data without appropriate institutional approvals and permission.

## 8. Release gate

Do not describe the software as biologically validated, clinically accurate, diagnostic, or ready for routine pathology use until independent validation has been completed and the dataset, protocol, performance metrics, confidence intervals, failure modes, and limitations are documented.

A passing unit-test suite establishes software behavior on its test cases only. It does not establish biological validity.


## 9. Additional validation for 3D morphometry

Before reporting a 3D volume fraction or surface-area descriptor:

- verify that the TIFF series axes are genuinely Z-Y-X and that channel/time axes have been selected explicitly;
- verify physical X/Y pixel sizes and the center-to-center Z sampling interval;
- document section thickness separately from inter-section spacing;
- preserve original section order and record any missing or damaged sections;
- assess and document serial-section registration error and tissue deformation;
- document any resampling, interpolation, or missing-section reconstruction;
- compare 3D labels against expert-reviewed reference volumes where feasible;
- perform sensitivity analyses for voxel spacing, segmentation boundaries, and section sampling interval.

The current toolkit does not register sections or reconstruct missing anatomy. Its 3D measurements assume that the input label volume is already spatially aligned. Surface area is a marching-cubes estimate and should be checked for resolution and discretization sensitivity.

## 10. Inter-annotator or segmentation agreement

Use the annotation-agreement module to compare two aligned label arrays. Prespecify which array is the reference, how disagreements are adjudicated, and which classes are primary.

Report per-class Dice and IoU together with prevalence and boundary-distance metrics (ASSD and Hausdorff-95). Include the physical pixel/voxel spacing and state the array axis order. Agreement metrics are not interchangeable with accuracy against biological truth; common systematic annotation errors can produce high agreement.
