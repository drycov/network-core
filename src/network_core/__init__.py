"""Shared network ops library."""

from network_core.vendor_identity import (
    normalize_vendor,
    infer_vendor,
    manufacturer_for_display,
)
from network_core.geo import distance_m

__all__ = [
    "normalize_vendor",
    "infer_vendor",
    "manufacturer_for_display",
    "distance_m",
]

__version__ = "0.1.0"
