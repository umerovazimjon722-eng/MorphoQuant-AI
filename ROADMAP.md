# Development roadmap

This roadmap describes intended work. Items are not considered complete until code, tests, documentation, and (where relevant) validation evidence are published.

## Milestone 0 — Reproducible mask-based analysis

**Status: implemented as an early prototype; independent biological validation remains outstanding.**

- [x] Installable Python package and command-line interface.
- [x] RGB image loading without modifying source files.
- [x] Strict loading of researcher-prepared grayscale masks.
- [x] Isotropic and anisotropic pixel calibration.
- [x] 2D connected-component morphometric measurements.
- [x] CSV output with explicit physical units.
- [x] JSON provenance sidecar and source/output checksums.
- [x] Descriptive statistics, Welch and Mann–Whitney comparisons, and Benjamini–Hochberg adjustment.
- [x] Automated tests and continuous integration workflow.
- [ ] Independent validation on expert-reviewed histological annotations.

## Milestone 1 — Acquisition metadata and quality control

- Add support for reading and preserving image metadata where available (for example, TIFF resolution and OME-TIFF metadata).
- Add explicit checks for missing, contradictory, or changed calibration.
- Record image dimensions, bit depth, file format, and processing history.
- Add image quality-control summaries without automatically excluding data.
- Define accepted formats and test them with synthetic and public-domain sample images.

**Acceptance criteria:** metadata extraction is covered by tests; calibration provenance is preserved; no physical unit is inferred from magnification alone.

## Milestone 2 — Annotation and segmentation evaluation

- Define an annotation protocol for adrenal cortex, medulla, vessels, and other relevant regions only where the scientific question requires them.
- Support expert-reviewed region-of-interest masks with an annotation provenance record.
- Establish independent annotator review and adjudication procedures.
- Evaluate proposed segmentation algorithms on a held-out dataset.
- Report Dice coefficient, intersection-over-union, boundary distance, object-level precision/recall, and uncertainty where appropriate.

**Acceptance criteria:** a segmentation method is not presented as validated until evaluated against independent expert annotations and its failure modes are documented.

## Milestone 3 — Sample-level study analysis

- Add structured import of experimental-design tables and sample identifiers.
- Add aggregation rules for fields nested within sections and biological specimens.
- Add mixed-effects or hierarchical models for nested and repeated-measures data.
- Add planned contrast and multiple-outcome reporting.
- Produce analysis tables that report biological sample size separately from numbers of sections, fields, cells, or objects.

**Acceptance criteria:** workflows explicitly represent the experimental unit and do not treat technical subsamples as independent biological replicates.

## Milestone 4 — Researcher-facing interface

- Explore integration with established image viewers such as napari.
- Provide reviewable overlays and editable annotations.
- Preserve links between source image, mask, measurement, and reviewer decision.
- Add accessible export formats and a reproducible project bundle.

**Acceptance criteria:** all edits are traceable; original images remain unchanged; users can reproduce measurements from the saved project bundle.

## Milestone 5 — External validation and release

- Publish a protocol and an appropriately licensed, de-identified or synthetic example dataset.
- Invite independent laboratories to test the workflow.
- Record external issues, code reviews, contributions, and reproducible bug reports.
- Prepare a versioned release only after the documented test and validation criteria are met.

**Acceptance criteria:** releases describe tested Python versions, dependencies, known limitations, validation datasets, and reproducible examples.

## Scope boundaries

MorphoQuant AI is a research software project. It is not a medical device and does not provide clinical diagnosis. Automated tissue segmentation, adrenal-zone classification, cell detection, and biological interpretation must not be claimed until the relevant capabilities are implemented and independently validated.
