# MorphoQuant AI

**An open-source research toolkit for quantitative histology and reproducible morphometric analysis.**

[![Tests](https://github.com/umerovazimjon722-eng/MorphoQuant-AI/actions/workflows/tests.yml/badge.svg)](https://github.com/umerovazimjon722-eng/MorphoQuant-AI/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![CodeQL](https://github.com/umerovazimjon722-eng/MorphoQuant-AI/actions/workflows/codeql.yml/badge.svg)](https://github.com/umerovazimjon722-eng/MorphoQuant-AI/actions/workflows/codeql.yml)

> **Development status:** Early research prototype. The current release provides mask-based morphometric measurements and provenance records. It is not an AI segmentation system, a validated diagnostic tool, or a medical device.

## Scientific motivation

Histological studies often combine manual microscopy measurements, image-processing software, spreadsheets, and statistical scripts. When calibration, segmentation, and measurement steps are not recorded consistently, results can be difficult to reproduce and compare.

MorphoQuant AI aims to provide transparent, modular, and testable workflows for quantitative histology. The first research use case is the morphometric assessment of adrenal gland tissue in experimental metabolic syndrome. The software is being designed to remain organ-agnostic where measurement methods can be appropriately validated.

## What works in this prototype

- Load microscopy images as RGB arrays without modifying the source file.
- Inspect TIFF/OME-TIFF metadata without loading full pixel planes; extract physical X/Y spacing when valid OME units or TIFF resolution units are present.
- Load researcher-prepared grayscale binary masks with explicit foreground rules.
- Require an explicit threshold for grayscale masks with more than two intensity values.
- Calibrate isotropic images or images with different horizontal and vertical pixel spacing.
- Measure 8-connected 2D components in binary masks: pixel area, physical area, digital contour perimeter, equivalent diameter, pixel and physical centroids, eccentricity, and solidity.
- Summarize researcher-annotated integer label masks class by class (for example, cortex and medulla), including area fraction, component count, component-size summaries, contour length, and area-weighted centroid.
- Create side-by-side PNG quality-control previews that overlay annotated classes on the original microscopy image, with boundaries and a class legend.
- Export measurements to a stable CSV schema.
- Write a JSON provenance sidecar containing input/output SHA-256 checksums, calibration, mask settings, software version, and measurement parameters.
- Run as an installable Python package or through a command-line interface.
- Summarize sample-level outcomes and compare two independent groups using Welch's t-test or Mann–Whitney U, with Benjamini–Hochberg p-value adjustment utilities.
- Execute automated tests on Python 3.10, 3.11, 3.12, and 3.13 through GitHub Actions.

**The package does not create the binary mask.** A researcher must supply a reviewed mask produced by manual annotation or a separately validated segmentation workflow. Automated tissue segmentation, adrenal-zone classification, cell detection, and diagnostic interpretation are not implemented.

## Installation

Python 3.10 or newer is required.

```bash
git clone https://github.com/umerovazimjon722-eng/MorphoQuant-AI.git
cd MorphoQuant-AI
python -m venv .venv

# Activate the environment:
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux:        source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
```

## Command-line usage

For a two-level grayscale binary mask (dark background, bright foreground):

```bash
morphoquant measure-mask sample_mask.png \
  --micrometers-per-pixel 0.25 \
  --output results/measurements.csv
```

For an image with different horizontal and vertical pixel sizes:

```bash
morphoquant measure-mask sample_mask.png \
  --micrometers-per-pixel-x 0.25 \
  --micrometers-per-pixel-y 0.27 \
  --output results/measurements.csv
```

For an anti-aliased grayscale mask, choose and document an appropriate threshold rather than relying on automatic binarization:

```bash
morphoquant measure-mask grayscale_mask.png \
  --threshold 127 \
  --foreground bright \
  --micrometers-per-pixel 0.25 \
  --min-area-px 10 \
  --output results/measurements.csv
```

The command creates a CSV file and, by default, a companion `measurements.metadata.json` file. Use `--metadata-output path.json` to choose another sidecar path. The JSON records checksums and analysis settings; it does not establish that the input mask is biologically correct.

For an already annotated integer label image (for example, class 1 = cortex and class 2 = medulla), create an optional class-name JSON file:

```json
{
  "1": "cortex",
  "2": "medulla"
}
```

Then run:

```bash
morphoquant measure-labels adrenal_zones.png \
  --micrometers-per-pixel-x 0.25 \
  --micrometers-per-pixel-y 0.27 \
  --class-names class_names.json \
  --background-label 0 \
  --min-area-px 20 \
  --output results/adrenal_zone_summary.csv
```

This command summarizes only the classes already present in the integer label image. It does not detect or assign cortex/medulla labels. It produces a class-summary CSV and a JSON provenance sidecar.

Create a side-by-side visual quality-control preview:

```bash
morphoquant overlay-labels adrenal_section.png adrenal_zones.png \
  --class-names class_names.json \
  --alpha 0.35 \
  --max-dimension 2400 \
  --output results/adrenal_zones_qc.png
```

The PNG includes the original image, a color overlay with boundaries, and a legend listing class IDs and pixel-area proportions. Large images are downscaled for preview only; quantitative measurements must use the original arrays. The tool visualizes supplied labels and does not segment tissue or infer class identity.

Run `morphoquant --help`, `morphoquant measure-mask --help`, `morphoquant measure-labels --help`, or `morphoquant overlay-labels --help` for all options.

## Python example

The morphometry function expects a **2D Boolean mask** in which `True` pixels represent a region already identified by a researcher or a validated segmentation method.

```python
import numpy as np
from morphoquant import MicroscopeCalibration, measure_binary_mask

# Synthetic example only; these are not experimental data.
mask = np.zeros((40, 40), dtype=bool)
mask[5:15, 8:28] = True

# Use the actual calibrated pixel size from your microscope.
calibration = MicroscopeCalibration(micrometers_per_pixel=0.25)
measurements = measure_binary_mask(mask, calibration)

for region in measurements:
    print(region)
```

The CLI can use OME-TIFF calibration directly when both physical X/Y scales and units are recorded:

```bash
morphoquant measure-mask binary_mask.ome.tif \
  --use-tiff-metadata \
  --output results/measurements.csv
```

Do not combine `--use-tiff-metadata` with manually supplied pixel sizes. If metadata is absent or incomplete, the command fails instead of guessing.

Inspect a TIFF/OME-TIFF file without loading the full image into memory:

```python
from morphoquant import read_tiff_metadata

metadata = read_tiff_metadata("adrenal_section.ome.tif")
print(metadata.to_dict())

# Only succeeds when valid physical sizes for both axes are present.
calibration = metadata.to_calibration()
```

For anisotropic pixel spacing:

```python
calibration = MicroscopeCalibration(
    micrometers_per_pixel_x=0.25,
    micrometers_per_pixel_y=0.27,
)
```

## Statistical analysis API

The `morphoquant.statistical_analysis` module provides descriptive summaries, two-group comparisons, and Benjamini–Hochberg false-discovery-rate adjustment.

```python
from morphoquant import (
    aggregate_subsamples_by_unit,
    compare_independent_groups,
    describe_samples,
    adjust_pvalues_bh,
)

# One value per independent biological replicate, not one value per microscope field.
control = [12.1, 11.8, 12.5, 11.9, 12.3]
treated = [14.0, 13.7, 14.4, 13.9, 14.1]

# If each animal has multiple fields, aggregate first:
field_records = [
    {"animal_id": "A1", "group": "control", "area": 10.0},
    {"animal_id": "A1", "group": "control", "area": 12.0},
    {"animal_id": "A2", "group": "control", "area": 11.0},
    {"animal_id": "B1", "group": "metabolic", "area": 15.0},
    {"animal_id": "B1", "group": "metabolic", "area": 17.0},
]
sample_level = aggregate_subsamples_by_unit(
    field_records,
    biological_unit_key="animal_id",
    measurement_key="area",
    group_key="group",
)
print(sample_level)

print(describe_samples(control))
print(compare_independent_groups(control, treated, method="welch"))

raw_p_values = [0.01, 0.04, 0.03]
print(adjust_pvalues_bh(raw_p_values))
```

Welch's test reports a confidence interval for the difference in means. Mann–Whitney reports a rank-biserial correlation and does not provide a median-difference confidence interval. Read [statistical methods](docs/statistical-methods.md) before interpreting the output. These functions do not replace study-specific statistical planning, assumption checks, mixed-effects models for repeated measurements, or adjustment for all sources of multiplicity. Avoid pseudoreplication: aggregate fields within each animal/sample or use a suitable hierarchical model.

## Output measurements and units

| Field | Unit / meaning |
|---|---|
| `label` | Connected-component identifier within this mask |
| `area_px2` | Foreground pixel count |
| `area_um2` | Physical area in square micrometres |
| `perimeter_px` | Marching-squares contour estimate in pixel units |
| `perimeter_um` | Contour estimate scaled by x/y pixel spacing |
| `equivalent_diameter_um` | Diameter of a circle with the same physical area |
| `centroid_x_px`, `centroid_y_px` | Centroid in image pixel coordinates |
| `centroid_x_um`, `centroid_y_um` | Centroid in calibrated physical coordinates |
| `pixel_size_x_um`, `pixel_size_y_um` | Calibration used for each image axis |
| `eccentricity` | Region shape descriptor |
| `solidity` | Region area divided by its convex-hull area |

Perimeter and shape descriptors depend on resolution, image preparation, connectivity, and boundary discretization. Do not compare values across studies unless the acquisition and analysis protocols are harmonized.

## Research integrity and limitations

- Calibration must come from a calibrated scale bar, acquisition metadata, or another documented procedure. OME-TIFF metadata is used only when both axis sizes and recognized physical units are present; missing or unknown units are never guessed. Do not infer it from image dimensions or a magnification label alone.
- The current analysis is 2D and uses 8-connectivity.
- A binary mask is an input, not a model prediction. Review masks against the source image.
- A passing software test verifies computational behavior on test cases; it does not establish biological validity or clinical utility.
- No biological conclusions should be inferred from synthetic examples.
- Real experimental data must be collected, handled, and shared under relevant institutional ethics approvals, privacy requirements, and animal-research standards.
- The software is a research-support tool, not a medical device and not a substitute for expert histopathological interpretation.

Read [methodological notes](docs/methodological-notes.md) before interpreting measurements. Use the [study record template](docs/analysis-protocol-template.md) to capture acquisition, calibration, annotation, quality assurance, and statistical-analysis details. Review the [research validation plan](docs/validation-plan.md) before using outputs in a biological study and the [development roadmap](ROADMAP.md) for future milestones. See [CHANGELOG.md](CHANGELOG.md) for the current prototype scope.

## Repository structure

```text
src/morphoquant/
├── __init__.py
├── calibration.py
├── image_io.py
├── tiff_metadata.py
├── masks.py
├── morphometry.py
├── labeled_morphometry.py
├── visualization.py
├── csv_export.py
├── provenance.py
└── cli.py
tests/
docs/
.github/workflows/
```

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md), the [Code of Conduct](CODE_OF_CONDUCT.md), and [Security Policy](SECURITY.md). Use the issue templates to report bugs or propose focused features. Pull requests should add tests, document units and assumptions, and report validation limitations.

Do not upload identifiable patient data, confidential laboratory records, credentials, or experimental data that have not been approved for public release.

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).
