# Histology morphometry study record template

Use one record per image or field of view. Complete this template before quantitative analysis. Do not include direct patient identifiers or confidential information in public files.

## Study and specimen

- Study identifier:
- Protocol/version:
- Ethics approval identifier (where applicable; do not publish confidential approvals):
- Species / strain or human tissue source:
- Organ:
- Experimental group:
- Sample identifier (coded/anonymized):
- Biological replicate identifier:
- Technical replicate / section identifier:
- Tissue collection date or batch (coded where needed):

## Tissue processing and staining

- Fixation:
- Processing and embedding:
- Section thickness (µm):
- Stain and protocol:
- Staining batch:
- Slide scanner or microscope:
- Objective / numerical aperture:
- Camera or scanner model:
- Image file format:
- Image bit depth:
- Image dimensions (rows × columns):

## Calibration

- Calibration method (stage micrometer, certified scale bar, acquisition metadata, other):
- Calibration date:
- Horizontal pixel size (µm/pixel):
- Vertical pixel size (µm/pixel):
- Isotropic pixels? (yes/no):
- Calibration source file or record:
- Image resizing/cropping performed after calibration? (describe):

Never derive physical pixel size from magnification alone. Recalibrate if the image has been resized or resampled.

## Image and region-of-interest record

- Original image filename:
- Original image SHA-256:
- Image processing performed (if any):
- Region-of-interest coordinates and coordinate convention:
- Excluded regions and reasons:
- Mask filename:
- Mask SHA-256:
- Mask creation method (manual, software-assisted, algorithm):
- Annotation software and version:
- Annotator code:
- Was the annotator blinded to experimental group? (yes/no/not applicable):
- Mask review / adjudication method:

## Morphometric analysis

- MorphoQuant AI version / commit:
- Python version:
- Dependency environment or lockfile:
- Connectivity (currently 8-connected for binary masks):
- Foreground rule:
- Threshold (if used):
- Minimum component area (pixels):
- Measurement descriptors:
- Output CSV filename and SHA-256:
- Output metadata JSON filename and SHA-256:

## Quality assurance and validation

- Number of images assessed:
- Number of biological replicates:
- Intra-observer repeatability method/results:
- Inter-observer agreement method/results:
- Expert-reviewed reference measurements:
- Agreement metrics and confidence intervals:
- Predefined exclusion criteria:
- Deviations from protocol:
- Known limitations:

## Statistical analysis plan

- Experimental unit:
- Primary outcome:
- Secondary outcomes:
- Planned group comparisons:
- Statistical test and rationale:
- Assumption checks:
- Multiple-comparison approach:
- Effect size and confidence interval method:
- Missing-data handling:
- Software and version used for statistics:

## Sign-off

- Analyst:
- Reviewer:
- Date:
- Notes:

This template is a record-keeping aid, not a substitute for institutional ethics approval, a preregistered protocol, or a validated laboratory SOP.
