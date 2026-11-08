# MorphoQuant AI

**An open-source research toolkit for quantitative histology and reproducible morphometric analysis.**

> **Development status:** Early prototype. This repository currently provides project documentation and a small set of foundational image-analysis utilities. It is not a validated diagnostic or clinical system.

## Scientific motivation

Histological studies often combine manual microscopy measurements, image-processing software, spreadsheets, and statistical scripts. When these steps are not documented consistently, analyses can be difficult to reproduce and compare.

MorphoQuant AI aims to provide transparent, modular, and testable workflows for quantitative histology. The initial research use case is the morphometric assessment of adrenal gland tissue in experimental metabolic syndrome. The methods are intended to be adaptable to other organs and tissue types after appropriate validation.

## Current prototype

The initial Python package focuses on foundational, non-AI functionality:

- explicit pixel-to-micrometre calibration;
- loading microscopy images without silently changing the source file;
- measurement of connected regions in researcher-supplied 2D binary masks;
- area, perimeter, equivalent diameter, centroid, eccentricity, and solidity outputs;
- unit-aware CSV-compatible tabular results;
- automated tests using synthetic masks.

The package does **not** automatically diagnose tissue, classify disease, identify adrenal zones, or segment histology images. Those capabilities would require annotated datasets, expert review, independent validation, and documented performance evaluation.

## Planned development

1. Establish validated image input, calibration, and quality-control procedures.
2. Add human-reviewed region-of-interest annotation and segmentation workflows.
3. Evaluate segmentation against expert annotations using pre-specified metrics.
4. Add reproducible statistical notebooks with explicit assumptions, effect sizes, and confidence intervals.
5. Add visualization and report-generation utilities with provenance tracking.
6. Expand to additional organs only when appropriate tissue-specific validation is available.

## Installation

Python 3.10 or newer is recommended.

```bash
git clone https://github.com/umerovazimjon722-eng/MorphoQuant-AI.git
cd MorphoQuant-AI
python -m venv .venv
# Activate the environment, then:
python -m pip install -e ".[dev]"
pytest
```

## Minimal example

The morphometry function expects a **2D Boolean mask** in which `True` pixels represent a region already identified by a researcher or another validated segmentation method.

```python
import numpy as np
from morphoquant.calibration import MicroscopeCalibration
from morphoquant.morphometry import measure_binary_mask

# Example only: a synthetic 20 x 10 pixel region, not experimental data.
mask = np.zeros((40, 40), dtype=bool)
mask[5:15, 8:28] = True

calibration = MicroscopeCalibration(micrometers_per_pixel=0.5)
measurements = measure_binary_mask(mask, calibration)

for region in measurements:
    print(region)
```

The example demonstrates software behavior only. It must not be interpreted as a biological observation or a validated measurement of real tissue.

## Research integrity and limitations

- All measurements depend on correct image calibration and valid input masks.
- Automated or manually prepared masks must be checked against source images by a qualified researcher.
- Perimeter estimates depend on the image-analysis implementation and pixel resolution; they should not be compared across studies without a consistent protocol.
- No biological conclusions should be inferred from synthetic data.
- Real experimental data must be collected, handled, and shared under relevant institutional ethics approvals, privacy requirements, and animal-research standards.
- The software is a research-support tool, not a medical device and not a substitute for expert histopathological interpretation.

## Repository structure

```text
src/morphoquant/
├── __init__.py
├── calibration.py
├── image_io.py
└── morphometry.py
tests/
README.md
pyproject.toml
```

## Contributing

Contributions are welcome. Please open an issue before proposing substantial changes. Contributions should include tests, documentation of units and assumptions, and a note describing limitations and validation requirements.

Do not upload identifiable patient data, confidential laboratory records, or experimental data that have not been approved for sharing.

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).
