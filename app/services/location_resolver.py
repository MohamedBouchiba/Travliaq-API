"""Service for resolving city names and geo coordinates to Viator destination IDs."""

from __future__ import annotations
import logging
from typing import Optional, Tuple
from rapidfuzz import fuzz, process
from motor.motor_asyncio import AsyncIOMotorCollection

logger = logging.getLogger(__name__)


class LocationResolver:
    """Resolve city names and geo coordinates to Viator destination IDs."""

    def __init__(self, destinations_collection: AsyncIOMotorCollection):
        """
        Initialize location resolver.

        Args:
            destinations_collection: MongoDB collection for destinations
        """
        self.destinations = destinations_collection
        self._cache = {}  # Simple in-memory cache for popular cities

    async def resolve_city(
        self,
        city: str,
        country_code: Optional[str] = None
    ) -> Optional[Tuple[str, str, float]]:
        """
        Resolve city name to Viator destination ID using fuzzy matching.

        Args:
            city: City name to search for
            country_code: ISO country code for filtering (optional but recommended)

        Returns:
            Tuple of (destination_id, matched_city_name, match_score) or None
        """
        # Check cache
        cache_key = f"{city.lower()}:{country_code or 'all'}"
        if cache_key in self._cache:
            logger.info(f"Cache hit for city resolution: {cache_key}")
            return self._cache[cache_key]

        # Build query
        query = {"type": "city"}
        if country_code:
            query["country_code"] = country_code.upper()

        # Fetch all cities (limited to 1000 for performance)
        cursor = self.destinations.find(query).limit(1000)
        cities = await cursor.to_list(length=1000)

        if not cities:
            logger.warning(
                f"No cities found in database for query: {query}. "
                f"Please run POST /admin/destinations/sync to populate the destinations collection."
            )
            return None

        # Fuzzy matching
        city_names = [c["name"] for c in cities]
        match = process.extractOne(
            city,
            city_names,
            scorer=fuzz.ratio,
            score_cutoff=80  # Minimum 80% match
        )

        if not match:
            logger.warning(f"No fuzzy match found for city '{city}'")
            return None

        matched_name, score, _ = match

        # Find destination ID
        matched_city = next(c for c in cities if c["name"] == matched_name)
        destination_id = matched_city["destination_id"]

        logger.info(f"Resolved '{city}' → '{matched_name}' (ID: {destination_id}, score: {score})")

        result = (destination_id, matched_name, score)
        self._cache[cache_key] = result

        return result

    async def resolve_geo(
        self,
        lat: float,
        lon: float,
        radius_km: float = 50
    ) -> Optional[Tuple[str, str, float]]:
        """
        Find nearest Viator destination using geospatial query.

        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in kilometers

        Returns:
            Tuple of (destination_id, city_name, distance_km) or None
        """
        # MongoDB geospatial query (requires 2dsphere index)
        query = {
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]  # [lon, lat] order for GeoJSON
                    },
                    "$maxDistance": radius_km * 1000  # Convert to meters
                }
            },
            "type": "city"
        }

        destination = await self.destinations.find_one(query)

        if not destination:
            logger.warning(f"No destination found within {radius_km}km of ({lat}, {lon})")
            return None

        # Calculate distance (approximation)
        from math import radians, cos, sin, asin, sqrt

        def haversine(lon1, lat1, lon2, lat2):
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))
            km = 6371 * c
            return km

        dest_coords = destination["location"]["coordinates"]
        distance_km = haversine(lon, lat, dest_coords[0], dest_coords[1])

        logger.info(
            f"Resolved geo ({lat}, {lon}) → '{destination['name']}' "
            f"(ID: {destination['destination_id']}, distance: {distance_km:.1f}km)"
        )

        return (destination["destination_id"], destination["name"], distance_km)
