# Methodological notes

## Pixel calibration

Morphometric measurements in physical units require a valid calibration for the image acquisition setup. The current prototype accepts an isotropic calibration value in micrometres per pixel. Obtain this value from a calibrated scale bar or microscope metadata and retain the calibration record with the image and analysis.

Do not infer calibration from image width, magnification labels alone, screenshots, or resized image dimensions. Resizing, scanning, compression, and export can change the relationship between pixels and physical distance.

The present implementation assumes equal physical scale along horizontal and vertical axes. Images with anisotropic pixel spacing require an explicitly extended calibration model before physical perimeter or shape measurements should be trusted.

## Binary masks and connected components

The current morphometry function does not segment tissue. It accepts a two-dimensional Boolean mask in which foreground pixels have already been defined by a researcher or another separately validated method. Connected components are measured with 8-connectivity.

The minimum-area filter is expressed in pixels. Area is converted to square micrometres using the square of the supplied pixel scale. Lengths and coordinates are converted using the same isotropic scale.

## Measurement interpretation

- Area is the count of foreground pixels in a connected component.
- Perimeter is the perimeter estimator returned by scikit-image and is resolution- and boundary-discretization-dependent.
- Equivalent diameter is the diameter of a circle with the same pixel area.
- Centroid coordinates are reported from the image origin, with x increasing by column and y increasing by row.
- Eccentricity and solidity are dimensionless region descriptors.

These are computational descriptors, not diagnoses or direct proxies for biological function. The suitability of each descriptor depends on tissue preparation, staining, image acquisition, segmentation quality, and the scientific question.

## Validation requirements

Before use in a research study, define a measurement protocol, calibrate the imaging system, assess intra- and inter-observer variability where relevant, compare computational outputs with expert-reviewed measurements, and document exclusions and uncertainty. Use blinded validation data where appropriate.

Synthetic unit tests verify software behavior only; they do not validate performance on biological tissue.
