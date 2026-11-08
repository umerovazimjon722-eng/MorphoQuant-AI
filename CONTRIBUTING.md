# Contributing to MorphoQuant AI

Thank you for considering a contribution.

## Before opening a pull request

1. Search existing issues and pull requests to avoid duplicate work.
2. For substantial changes, open an issue describing the scientific or software problem first.
3. Keep changes focused and explain the motivation.

## Code quality

- Use clear names, type hints where useful, and docstrings for public functions.
- Add automated tests for new behavior and regression fixes.
- Keep units explicit. Never assume pixel calibration when it has not been supplied.
- Do not silently alter source microscopy images or experimental measurements.
- Document algorithms, parameters, exclusions, and known limitations.

## Scientific validation

A passing software test does not establish biological validity. Image-analysis methods must be evaluated on appropriate datasets and compared with expert-reviewed annotations or measurements. Report the validation design, sample characteristics, metrics, uncertainty, and limitations.

Do not submit claims of diagnostic accuracy or clinical utility without appropriate independent validation and regulatory review.

## Data and privacy

Do not commit identifiable patient data, confidential laboratory records, credentials, or experimental data that are not approved for public release. Use synthetic or properly de-identified example data with documented provenance.

## Pull requests

Describe:
- the problem being addressed;
- the approach and relevant assumptions;
- tests performed and their results;
- any changes to units, outputs, or compatibility;
- remaining limitations.
