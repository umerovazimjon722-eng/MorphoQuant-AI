"""Metadata inspection for TIFF and OME-TIFF microscopy images."""

from dataclasses import asdict, dataclass
import math
from pathlib import Path
from typing import Dict, Optional, Union
import xml.etree.ElementTree as ET

import tifffile

from .calibration import MicroscopeCalibration

PathLike = Union[str, Path]

_LENGTH_TO_UM = {
    "m": 1_000_000.0,
    "cm": 10_000.0,
    "mm": 1_000.0,
    "um": 1.0,
    "µm": 1.0,
    "μm": 1.0,
    "micrometer": 1.0,
    "micrometre": 1.0,
    "nm": 0.001,
    "angstrom": 0.0001,
    "å": 0.0001,
}


def _to_um(value: object, unit: object) -> Optional[float]:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric) or numeric <= 0:
        return None
    if not isinstance(unit, str):
        return None
    factor = _LENGTH_TO_UM.get(unit.strip().lower())
    if factor is None:
        return None
    return numeric * factor


def _ome_pixel_sizes(xml_text: str | None) -> tuple[Optional[float], Optional[float]]:
    if not xml_text:
        return None, None
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None, None

    pixels = next(
        (element for element in root.iter() if element.tag.rsplit("}", 1)[-1] == "Pixels"),
        None,
    )
    if pixels is None:
        return None, None

    x = _to_um(pixels.attrib.get("PhysicalSizeX"), pixels.attrib.get("PhysicalSizeXUnit"))
    y = _to_um(pixels.attrib.get("PhysicalSizeY"), pixels.attrib.get("PhysicalSizeYUnit"))
    return x, y


@dataclass(frozen=True)
class TiffImageMetadata:
    """Small metadata record extracted without reading pixel planes into memory."""

    file_name: str
    shape: tuple[int, ...]
    axes: str
    dtype: str
    series_count: int
    is_ome_tiff: bool
    pixel_size_x_um: Optional[float]
    pixel_size_y_um: Optional[float]

    @property
    def has_physical_calibration(self) -> bool:
        """Whether both X and Y physical pixel spacings were found."""
        return self.pixel_size_x_um is not None and self.pixel_size_y_um is not None

    @property
    def is_isotropic(self) -> Optional[bool]:
        """Whether the extracted X and Y pixel spacings are equal."""
        if not self.has_physical_calibration:
            return None
        return math.isclose(
            float(self.pixel_size_x_um),
            float(self.pixel_size_y_um),
            rel_tol=0.0,
            abs_tol=1e-12,
        )

    def to_calibration(self) -> MicroscopeCalibration:
        """Create an explicit calibration or raise if metadata is incomplete."""
        if not self.has_physical_calibration:
            raise ValueError(
                "TIFF metadata does not contain valid physical pixel sizes for both X and Y. "
                "Calibrate the image independently; do not infer scale from magnification."
            )
        return MicroscopeCalibration(
            micrometers_per_pixel_x=float(self.pixel_size_x_um),
            micrometers_per_pixel_y=float(self.pixel_size_y_um),
        )

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serializable metadata dictionary."""
        record = asdict(self)
        record["shape"] = list(self.shape)
        record["has_physical_calibration"] = self.has_physical_calibration
        record["is_isotropic"] = self.is_isotropic
        return record


def read_tiff_metadata(path: PathLike) -> TiffImageMetadata:
    """Read TIFF/OME-TIFF series metadata and physical X/Y pixel sizes.

    This function does not decode the full image array. It inspects the first
    TIFF series. For OME-TIFF, physical spacing is read from OME-XML. For
    ordinary TIFF, calibrated resolution tags are accepted when their unit is
    explicitly inches or centimetres. Unknown/missing units yield no scale.

    Multi-series files are reported with the total series count; the shape,
    axes, dtype, and physical pixel sizes refer to the first series only.
    """
    image_path = Path(path)
    if not image_path.is_file():
        raise FileNotFoundError(f"TIFF image does not exist: {image_path}")

    try:
        with tifffile.TiffFile(image_path) as tiff:
            if not tiff.series:
                raise ValueError("TIFF file contains no readable image series.")
            series = tiff.series[0]
            shape = tuple(int(item) for item in series.shape)
            axes = str(series.axes)
            dtype = str(series.dtype)
            ome_xml = tiff.ome_metadata
            x_um, y_um = _ome_pixel_sizes(ome_xml)

            if x_um is None or y_um is None:
                first_page = tiff.pages[0]
                x_resolution = first_page.tags.get("XResolution")
                y_resolution = first_page.tags.get("YResolution")
                resolution_unit = first_page.tags.get("ResolutionUnit")
                unit_code = resolution_unit.value if resolution_unit is not None else 1

                def from_resolution(tag: object) -> Optional[float]:
                    if tag is None or unit_code not in (2, 3):
                        return None
                    try:
                        numerator, denominator = tag.value
                        pixels_per_unit = float(numerator) / float(denominator)
                    except (TypeError, ValueError, ZeroDivisionError):
                        return None
                    if not math.isfinite(pixels_per_unit) or pixels_per_unit <= 0:
                        return None
                    micrometers_per_unit = 25_400.0 if unit_code == 2 else 10_000.0
                    return micrometers_per_unit / pixels_per_unit

                # Use the TIFF resolution tags only when both axes are available.
                tag_x_um = from_resolution(x_resolution)
                tag_y_um = from_resolution(y_resolution)
                if tag_x_um is not None and tag_y_um is not None:
                    x_um, y_um = tag_x_um, tag_y_um

            return TiffImageMetadata(
                file_name=image_path.name,
                shape=shape,
                axes=axes,
                dtype=dtype,
                series_count=len(tiff.series),
                is_ome_tiff=bool(ome_xml),
                pixel_size_x_um=x_um,
                pixel_size_y_um=y_um,
            )
    except (tifffile.TiffFileError, OSError) as exc:
        raise ValueError(f"Could not read TIFF metadata: {image_path}") from exc
