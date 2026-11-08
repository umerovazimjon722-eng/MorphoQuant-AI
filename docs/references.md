# Scientific and technical references

This list documents the principal software and methodological sources relevant to the current prototype. It is not a systematic literature review and does not replace a study-specific literature search.

## Scientific image formats and acquisition metadata

1. Goldberg, I. G., Allan, C., Burel, J.-M., Creager, D., Falconi, A., Hochheiser, H., Johnston, J., Mellen, J., et al. (2005). The Open Microscopy Environment (OME) Data Model and XML file: open tools for informatics and quantitative analysis in biological imaging. *Genome Biology, 6*, R47. https://doi.org/10.1186/gb-2005-6-5-r47

2. Open Microscopy Environment. (n.d.). *OME-TIFF specification*. https://github.com/ome/ome-model-documentation/blob/main/ome-tiff/specification.rst

The project reads a deliberately narrow OME-TIFF subset for 3D analysis: one selected image series with axes exactly Z-Y-X and explicit physical X/Y/Z spacing. The specification is broader than the current reader. Unsupported dimensions, series, metadata combinations, or units must be handled explicitly rather than guessed.

## Image processing software

3. van der Walt, S., Schönberger, J. L., Nunez-Iglesias, J., Boulogne, F., Warner, J. D., Yager, N., Gouillart, E., & Yu, T. (2014). scikit-image: image processing in Python. *PeerJ, 2*, e453. https://doi.org/10.7717/peerj.453

4. Bankhead, P., Loughrey, M. B., Fernández, J. A., Dombrowski, Y., McArt, D. G., Dunne, P. D., McQuaid, S., Gray, R. T., Murray, L. J., Coleman, H. G., James, J. A., Salto-Tellez, M., & Hamilton, P. W. (2017). QuPath: Open source software for digital pathology image analysis. *Scientific Reports, 7*, 16878. https://doi.org/10.1038/s41598-017-17204-5

MorphoQuant AI uses scikit-image for connected-component properties, contour/surface extraction, and other image-analysis primitives. QuPath is a relevant established digital pathology platform and a potential integration point; this project does not claim feature parity with QuPath.

## Segmentation and annotation agreement

5. Taha, A. A., & Hanbury, A. (2015). Metrics for evaluating 3D medical image segmentation: analysis, selection, and tool. *BMC Medical Imaging, 15*, 29. https://doi.org/10.1186/s12880-015-0068-x

6. Müller, D., Soto-Rey, I., & Kramer, F. (2022). Towards a guideline for evaluation metrics in medical image segmentation. *BMC Research Notes, 15*, 210. https://doi.org/10.1186/s13104-022-06096-y

These works discuss the complementary behavior and limitations of overlap- and distance-based metrics. MorphoQuant AI reports multiple metrics per class rather than treating any single score as sufficient evidence of anatomical accuracy. The selected metrics and empty-class conventions are software choices that must be reported and validated for each study.

## Agreement between continuous measurement methods

7. Bland, J. M., & Altman, D. G. (1986). Statistical methods for assessing agreement between two methods of clinical measurement. *The Lancet, 1*(8476), 307–310. https://doi.org/10.1016/S0140-6736(86)90837-8

8. Bland, J. M., & Altman, D. G. (1999). Measuring agreement in method comparison studies. *Statistical Methods in Medical Research, 8*(2), 135–160. https://doi.org/10.1177/096228029900800204

Bland–Altman analysis is relevant when comparing continuous measurements obtained by two observers or two methods on the same specimens. It is not interchangeable with Dice/IoU or surface-distance metrics for comparing label masks. Correlation alone does not establish agreement.

## Scope and citation practice

- Cite the specific software version and repository commit used for an analysis.
- Cite the original methods and software sources that are actually used in the study.
- Report calibration, image axes, connectivity, filtering, annotation protocol, experimental unit, exclusions, and validation design.
- Do not cite synthetic examples as biological evidence.
- Do not describe this prototype as clinically validated, diagnostically accurate, or as an automated segmentation model.
