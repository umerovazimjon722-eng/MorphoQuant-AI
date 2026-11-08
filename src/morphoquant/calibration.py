"""Explicit microscope calibration and pixel-to-physical unit conversions."""

from dataclasses import dataclass
import math
from numbers import Real
from typing import Literal


def _positive_finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number.")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be finite and greater than zero.")
    return result


@dataclass(frozen=True)
class MicroscopeCalibration:
    """Pixel spacing for a microscopy image.

    Supply either one isotropic scale or both axis-specific scales.

    Examples
    --------
    >>> MicroscopeCalibration(micrometers_per_pixel=0.25)
    >>> MicroscopeCalibration(
    ...     micrometers_per_pixel_x=0.25,
    ...     micrometers_per_pixel_y=0.27,
    ... )

    Values must come from a calibrated scale bar, acquisition metadata, or
    another documented calibration procedure. Never infer them from image
    dimensions or an unverified magnification label.
    """

    micrometers_per_pixel: float | None = None
    micrometers_per_pixel_x: float | None = None
    micrometers_per_pixel_y: float | None = None

    @classmethod
    def from_isotropic_reference(
        cls,
        *,
        reference_pixels: float,
        reference_length_um: float,
    ) -> "MicroscopeCalibration":
        """Build an isotropic calibration from a measured scale-bar length.

        reference_pixels is the measured scale-bar length in image pixels;
        reference_length_um is its stated physical length in micrometres.
        Use this only when isotropic pixel spacing is justified. For
        anisotropic images, provide independently measured X and Y scales.
        """
        pixels = _positive_finite(reference_pixels, "reference_pixels")
        length = _positive_finite(reference_length_um, "reference_length_um")
        return cls(micrometers_per_pixel=length / pixels)

    def __post_init__(self) -> None:
        if self.micrometers_per_pixel is not None:
            if (
                self.micrometers_per_pixel_x is not None
                or self.micrometers_per_pixel_y is not None
            ):
                raise ValueError(
                    "Use either micrometers_per_pixel or both axis-specific scales, not both."
                )
            _positive_finite(self.micrometers_per_pixel, "micrometers_per_pixel")
            return

        if self.micrometers_per_pixel_x is None or self.micrometers_per_pixel_y is None:
            raise ValueError(
                "Provide micrometers_per_pixel or both micrometers_per_pixel_x "
                "and micrometers_per_pixel_y."
            )
        _positive_finite(self.micrometers_per_pixel_x, "micrometers_per_pixel_x")
        _positive_finite(self.micrometers_per_pixel_y, "micrometers_per_pixel_y")

    @property
    def scale_x_um(self) -> float:
        """Physical width represented by one column, in micrometres."""
        if self.micrometers_per_pixel is not None:
            return float(self.micrometers_per_pixel)
        return float(self.micrometers_per_pixel_x)

    @property
    def scale_y_um(self) -> float:
        """Physical height represented by one row, in micrometres."""
        if self.micrometers_per_pixel is not None:
            return float(self.micrometers_per_pixel)
        return float(self.micrometers_per_pixel_y)

    @property
    def is_isotropic(self) -> bool:
        """Whether horizontal and vertical pixel spacing are equal."""
        return math.isclose(self.scale_x_um, self.scale_y_um, rel_tol=0.0, abs_tol=1e-12)

    def length_um(self, pixels: float, *, axis: Literal["x", "y"] = "x") -> float:
        """Convert a length along the specified image axis to micrometres."""
        if isinstance(pixels, bool) or not isinstance(pixels, Real):
            raise TypeError("pixels must be a real number.")
        if not math.isfinite(float(pixels)) or pixels < 0:
            raise ValueError("pixels must be finite and non-negative.")
        if axis == "x":
            scale = self.scale_x_um
        elif axis == "y":
            scale = self.scale_y_um
        else:
            raise ValueError("axis must be 'x' or 'y'.")
        return float(pixels * scale)

    def area_um2(self, square_pixels: float) -> float:
        """Convert pixel area to square micrometres using both axis scales."""
        if isinstance(square_pixels, bool) or not isinstance(square_pixels, Real):
            raise TypeError("square_pixels must be a real number.")
        if not math.isfinite(float(square_pixels)) or square_pixels < 0:
            raise ValueError("square_pixels must be finite and non-negative.")
        return float(square_pixels * self.scale_x_um * self.scale_y_um)
