# Examples

All examples in this directory are synthetic software demonstrations. They are not biological observations and must not be used as experimental results.

## Adrenal-zone label morphometry

Install the package and run:

```bash
python -m pip install -e .
python examples/synthetic_adrenal_zones.py
```

The example creates an artificial integer label image with two classes, supplies a demonstration calibration, and prints class-wise morphometric summaries.

Replace the synthetic label image with an expert-reviewed, ethically shareable annotation and replace the demonstration scale with measured microscope calibration before using the workflow in research.
