# Changelog

All notable project changes are documented here.

## 0.1.0 — Initial research prototype

- Added explicit isotropic and anisotropic microscope pixel calibration.
- Added RGB image loading and strict grayscale binary-mask loading.
- Added 2D connected-component morphometry for researcher-provided Boolean masks.
- Added calibrated area, contour perimeter, equivalent diameter, centroid, eccentricity, and solidity measurements.
- Added stable CSV export.
- Added JSON analysis provenance with input and output SHA-256 checksums.
- Added class-wise morphometry for researcher-annotated integer label masks, including tissue-zone summaries and area fractions.
- Added TIFF/OME-TIFF metadata inspection and safe extraction of physical pixel calibration when units are explicit.
- Added isotropic calibration derivation from a measured scale bar.
- Added a `measure-labels` CLI workflow with class-name JSON input, class-summary CSV output, and provenance metadata.
- Added sample-level descriptive summaries, Welch and Mann–Whitney independent-group comparisons, and Benjamini–Hochberg FDR adjustment.
- Added a command-line interface through the `morphoquant` command.
- Added automated tests and a GitHub Actions Python-version matrix.
- Added methodological notes, a histology analysis record template, a validation plan, and a milestone-based development roadmap.

This release does not perform automated tissue segmentation, cell detection, adrenal-zone classification, machine-learning inference, or clinical diagnosis. It is an early research prototype.
