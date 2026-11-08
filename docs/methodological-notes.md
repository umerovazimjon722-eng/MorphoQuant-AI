# Methodological notes

## Pixel calibration

Morphometric measurements in physical units require a valid calibration for the image acquisition setup. The current prototype accepts an isotropic calibration value in micrometres per pixel. Obtain this value from a calibrated scale bar or microscope metadata and retain the calibration record with the image and analysis.

Do not infer calibration from image width, magnification labels alone, screenshots, or resized image dimensions. Resizing, scanning, compression, and export can change the relationship between pixels and physical distance.

The calibration model accepts either one isotropic scale or separate horizontal and vertical pixel spacings. When these differ, the implementation supplies both axes to region-based shape descriptors and scales contour coordinates independently. Do not force anisotropic images into a single averaged pixel size.

## Binary masks and connected components

The current morphometry function does not segment tissue. It accepts a two-dimensional Boolean mask in which foreground pixels have already been defined by a researcher or another separately validated method. Connected components are measured with 8-connectivity.

The minimum-area filter is expressed in pixels. Area is converted to square micrometres using the square of the supplied pixel scale. Lengths and coordinates are converted using the same isotropic scale.

## Measurement interpretation

- Area is the count of foreground pixels in a connected component.
- Perimeter is estimated from 0.5-level marching-squares contours. Physical contour segments are scaled independently along the horizontal and vertical axes. The estimate remains resolution- and boundary-discretization-dependent.
- Equivalent diameter is the diameter of a circle with the same pixel area.
- Centroid coordinates are reported from the image origin, with x increasing by column and y increasing by row.
- Eccentricity and solidity are dimensionless region descriptors.

These are computational descriptors, not diagnoses or direct proxies for biological function. The suitability of each descriptor depends on tissue preparation, staining, image acquisition, segmentation quality, and the scientific question.

## Validation requirements

Before use in a research study, define a measurement protocol, calibrate the imaging system, assess intra- and inter-observer variability where relevant, compare computational outputs with expert-reviewed measurements, and document exclusions and uncertainty. Use blinded validation data where appropriate.

Synthetic unit tests verify software behavior only; they do not validate performance on biological tissue.


## Multi-class label masks

The class-wise morphometry module accepts an integer label image. Each pixel must contain a non-negative integer class ID; one ID is designated as background and excluded. The software does not infer what a class represents. Names such as "cortex" and "medulla" are researcher-supplied labels and must follow a documented annotation protocol.

Each class is split into 8-connected components. Components smaller than the configured pixel-area threshold are excluded from that class summary. The reported class area percentage is calculated among the retained non-background components across all classes, not relative to the entire image. Component counts refer to connected image objects, not independent biological replicates.

Area-weighted centroid coordinates summarize the spatial location of the retained class pixels. The reported aggregate perimeter is the sum of component contour estimates. It is not a measure of a closed anatomical boundary where the mask contains disconnected islands or holes.

Before comparing class percentages between specimens, ensure that field-of-view selection, section orientation, tissue sampling, and annotation criteria are harmonized. A 2D area fraction is not automatically equivalent to a 3D volume fraction.


## TIFF and OME-TIFF metadata

The TIFF metadata reader inspects the first image series without loading all pixel planes into memory. It reports the series shape, axes, data type, number of series, and whether OME-XML is present.

Physical X/Y pixel spacing is accepted from OME-XML only when both values and recognized length units are available. For plain TIFF, resolution tags are accepted only when the resolution unit explicitly specifies inches or centimetres. If the unit is absent, unknown, or incomplete, no physical calibration is returned.

Metadata-derived spacing should still be checked against the microscope acquisition record or a calibrated scale. Cropping, resizing, resampling, export, or conversion can invalidate the original physical pixel size. For multi-series TIFF files, the current reader reports calibration for the first series only; inspect each series separately before treating a multi-series acquisition as one calibrated image.

## Calibration from a scale bar

The helper `MicroscopeCalibration.from_isotropic_reference` computes micrometres per pixel as physical reference length divided by the measured scale-bar length in pixels. Use this only when equal X and Y pixel spacing is justified. If X and Y spacing differ, measure both axes independently and provide both calibration values.

Do not use a scale bar that has been resized independently of the image or whose physical label/provenance cannot be verified.


## Visual quality-control overlays

The visualization helper renders two panels from an RGB source image and an integer annotation mask: the original image and a color overlay with class boundaries and a legend. It does not alter the source arrays or infer class identities. Color assignment is deterministic for a given sorted set of class IDs.

For memory control, previews can be downscaled to a maximum panel dimension. Downscaled output is for visual review only; do not use the preview pixels for quantitative measurement. Run morphometry on the original-resolution label mask with the original calibration metadata. Review overlays against the original image before accepting quantitative results.
