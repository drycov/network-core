"""Geo helpers shared by field and inventory products."""
from __future__ import annotations

from haversine import Unit, haversine


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance between two WGS84 points in meters."""
    return haversine((lat1, lon1), (lat2, lon2), unit=Unit.METERS)
