"""Unit conversions based on a documented microscope calibration."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class MicroscopeCalibration:
    """Isotropic image calibration.

    Parameters
    ----------
    micrometers_per_pixel:
        Physical length represented by one image pixel, in micrometres.
        Obtain this value from a calibrated scale bar or microscope metadata.
        Do not guess or infer it from image dimensions.
    """

    micrometers_per_pixel: float

    def __post_init__(self) -> None:
        value = self.micrometers_per_pixel
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("micrometers_per_pixel must be a real number.")
        if not math.isfinite(value) or value <= 0:
            raise ValueError("micrometers_per_pixel must be finite and greater than zero.")

    def length_um(self, pixels: float) -> float:
        """Convert a pixel length to micrometres."""
        if not math.isfinite(pixels) or pixels < 0:
            raise ValueError("pixels must be finite and non-negative.")
        return float(pixels * self.micrometers_per_pixel)

    def area_um2(self, square_pixels: float) -> float:
        """Convert a pixel area to square micrometres."""
        if not math.isfinite(square_pixels) or square_pixels < 0:
            raise ValueError("square_pixels must be finite and non-negative.")
        return float(square_pixels * self.micrometers_per_pixel**2)
