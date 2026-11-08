# MorphoQuant AI

**An open-source research toolkit for quantitative histology and reproducible morphometric analysis.**

[![Tests](https://github.com/umerovazimjon722-eng/MorphoQuant-AI/actions/workflows/tests.yml/badge.svg)](https://github.com/umerovazimjon722-eng/MorphoQuant-AI/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)

> **Development status:** Early research prototype. The current release provides mask-based morphometric measurements and provenance records. It is not an AI segmentation system, a validated diagnostic tool, or a medical device.

## Scientific motivation

Histological studies often combine manual microscopy measurements, image-processing software, spreadsheets, and statistical scripts. When calibration, segmentation, and measurement steps are not recorded consistently, results can be difficult to reproduce and compare.

MorphoQuant AI aims to provide transparent, modular, and testable workflows for quantitative histology. The first research use case is the morphometric assessment of adrenal gland tissue in experimental metabolic syndrome. The software is being designed to remain organ-agnostic where measurement methods can be appropriately validated.

## What works in this prototype

- Load microscopy images as RGB arrays without modifying the source file.
- Load researcher-prepared grayscale binary masks with explicit foreground rules.
- Require an explicit threshold for grayscale masks with more than two intensity values.
- Calibrate isotropic images or images with different horizontal and vertical pixel spacing.
- Measure 8-connected 2D components: pixel area, physical area, digital contour perimeter, equivalent diameter, pixel and physical centroids, eccentricity, and solidity.
- Export measurements to a stable CSV schema.
- Write a JSON provenance sidecar containing input/output SHA-256 checksums, calibration, mask settings, software version, and measurement parameters.
- Run as an installable Python package or through a command-line interface.
- Execute automated tests on Python 3.10, 3.11, and 3.12 through GitHub Actions.

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

For a two-level grayscale mask (dark background, bright foreground):

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

Run `morphoquant --help` or `morphoquant measure-mask --help` for all options.

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

For anisotropic pixel spacing:

```python
calibration = MicroscopeCalibration(
    micrometers_per_pixel_x=0.25,
    micrometers_per_pixel_y=0.27,
)
```

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

- Calibration must come from a calibrated scale bar, acquisition metadata, or another documented procedure. Do not infer it from image dimensions or a magnification label alone.
- The current analysis is 2D and uses 8-connectivity.
- A binary mask is an input, not a model prediction. Review masks against the source image.
- A passing software test verifies computational behavior on test cases; it does not establish biological validity or clinical utility.
- No biological conclusions should be inferred from synthetic examples.
- Real experimental data must be collected, handled, and shared under relevant institutional ethics approvals, privacy requirements, and animal-research standards.
- The software is a research-support tool, not a medical device and not a substitute for expert histopathological interpretation.

Read [methodological notes](docs/methodological-notes.md) before interpreting measurements.

## Repository structure

```text
src/morphoquant/
├── __init__.py
├── calibration.py
├── image_io.py
├── masks.py
├── morphometry.py
├── csv_export.py
├── provenance.py
└── cli.py
tests/
docs/
.github/workflows/
```

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md), open an issue before substantial changes, add tests, document units and assumptions, and report validation limitations.

Do not upload identifiable patient data, confidential laboratory records, credentials, or experimental data that have not been approved for public release.

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).
