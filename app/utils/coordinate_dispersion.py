"""
Deterministic coordinate dispersion for activities without precise locations.

This module provides a "GeoGuessr-style" intelligent distribution system that:
- Makes coordinates look natural on a map (not all clustered at city center)
- Is deterministic (same activity always gets same coordinates)
- Uses hash-based seeding for varied but repeatable distribution
- Applies sqrt distribution for realistic clustering near center
"""

from __future__ import annotations
import hashlib
import math
from typing import Tuple


def generate_dispersed_coordinates(
    activity_id: str,
    destination_id: str,
    city_center: dict,
    city_radius_km: float
) -> dict:
    """
    Generate deterministic but varied coordinates using hash-based seeding.

    Strategy:
    - Hash activity_id + destination_id → deterministic seed
    - Extract angle (0-360°) and distance factor (0-1)
    - Apply sqrt distribution (cluster more near center, realistic)
    - Convert to lat/lon offset

    Args:
        activity_id: Unique activity identifier (e.g., product code)
        destination_id: Viator destination ID
        city_center: Dict with {"lat": float, "lon": float}
        city_radius_km: Maximum dispersion radius from center

    Returns:
        Dict containing:
        - coordinates: {"lat": float, "lon": float}
        - precision: "dispersed"
        - source: "deterministic_hash"
        - offset_km: Distance from city center
        - angle_degrees: Angle from city center

    Example:
        >>> center = {"lat": 48.8566, "lon": 2.3522}  # Paris
        >>> result = generate_dispersed_coordinates("183050P6", "479", center, 5.0)
        >>> result["coordinates"]
        {"lat": 48.8612, "lon": 2.3601}  # Offset from center
        >>> result["precision"]
        "dispersed"
    """
    # Deterministic seed
    seed_string = f"{activity_id}:{destination_id}"
    hash_bytes = hashlib.md5(seed_string.encode()).digest()

    # Extract angle (0-360°)
    angle_seed = int.from_bytes(hash_bytes[0:4], byteorder='big')
    angle_degrees = angle_seed % 360

    # Extract distance factor (0-1), apply sqrt for natural clustering
    distance_seed = int.from_bytes(hash_bytes[4:8], byteorder='big')
    distance_factor = (distance_seed % 1000) / 1000.0
    distance_km = city_radius_km * math.sqrt(distance_factor)  # sqrt = cluster near center

    # Convert polar to Cartesian offset
    lat_offset, lon_offset = polar_to_cartesian_offset(
        distance_km,
        angle_degrees,
        city_center["lat"]
    )

    return {
        "coordinates": {
            "lat": city_center["lat"] + lat_offset,
            "lon": city_center["lon"] + lon_offset
        },
        "precision": "dispersed",
        "source": "deterministic_hash",
        "offset_km": round(distance_km, 2),
        "angle_degrees": angle_degrees
    }


def polar_to_cartesian_offset(
    distance_km: float,
    angle_degrees: float,
    reference_lat: float
) -> Tuple[float, float]:
    """
    Convert polar (distance, angle) to lat/lon offsets.

    Accounts for latitude compression (longitude degrees get smaller near poles).

    Args:
        distance_km: Distance from reference point in kilometers
        angle_degrees: Angle from north (0° = north, 90° = east)
        reference_lat: Reference latitude for longitude compression

    Returns:
        Tuple of (lat_offset, lon_offset) in degrees

    Example:
        >>> polar_to_cartesian_offset(5.0, 45, 48.8566)
        (0.032, 0.048)  # Approx 5km at 45° from Paris center
    """
    R = 6371.0  # Earth radius in kilometers
    angle_rad = math.radians(angle_degrees)

    # Latitude offset (simple, no compression)
    lat_offset = (distance_km / R) * (180 / math.pi) * math.sin(angle_rad)

    # Longitude offset (compressed by latitude)
    lon_offset = (distance_km / (R * math.cos(math.radians(reference_lat)))) * (180 / math.pi) * math.cos(angle_rad)

    return (lat_offset, lon_offset)


def validate_dispersed_coordinates(
    coordinates: dict,
    city_center: dict,
    max_radius_km: float
) -> bool:
    """
    Validate that dispersed coordinates are within acceptable range.

    Args:
        coordinates: {"lat": float, "lon": float}
        city_center: {"lat": float, "lon": float}
        max_radius_km: Maximum allowed distance from center

    Returns:
        True if coordinates are valid, False otherwise
    """
    # Calculate distance using haversine
    distance = _haversine_distance(
        city_center["lat"], city_center["lon"],
        coordinates["lat"], coordinates["lon"]
    )

    return distance <= max_radius_km


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula.

    Args:
        lat1, lon1: First point
        lat2, lon2: Second point

    Returns:
        Distance in kilometers
    """
    R = 6371.0  # Earth radius km

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return R * c
