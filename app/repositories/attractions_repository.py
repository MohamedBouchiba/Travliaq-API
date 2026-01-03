"""MongoDB repository for attractions.

This repository handles attractions data including the critical reverse lookup:
productCode → attraction → coordinates (for LEVEL 2 enrichment).
"""

from __future__ import annotations
import logging
from typing import Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorCollection

logger = logging.getLogger(__name__)


class AttractionsRepository:
    """Repository for attractions collection in MongoDB."""

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    @staticmethod
    def _convert_coordinates_to_geojson(data: dict) -> dict:
        """
        Convert coordinates from {lat, lon} format to GeoJSON format for MongoDB 2dsphere index.

        MongoDB 2dsphere indexes require GeoJSON format: [longitude, latitude]
        But our data comes in as: {lat: ..., lon: ...}

        Args:
            data: Attraction data with location.coordinates

        Returns:
            Modified data with GeoJSON coordinates
        """
        if "location" in data and "coordinates" in data["location"]:
            coords = data["location"]["coordinates"]

            # Check if coordinates are in {lat, lon} format
            if isinstance(coords, dict) and "lat" in coords and "lon" in coords:
                # Convert to GeoJSON Point format: [longitude, latitude]
                data["location"]["coordinates"] = [coords["lon"], coords["lat"]]
                logger.debug(
                    f"Converted coordinates from {{lat: {coords['lat']}, lon: {coords['lon']}}} "
                    f"to GeoJSON: [{coords['lon']}, {coords['lat']}]"
                )

        return data

    @staticmethod
    def _convert_geojson_to_coordinates(data: dict) -> dict:
        """
        Convert coordinates from GeoJSON format [lon, lat] back to {lat, lon} format.

        This is used when reading from MongoDB to maintain compatibility with existing code.

        Args:
            data: Attraction data with GeoJSON coordinates

        Returns:
            Modified data with {lat, lon} coordinates
        """
        if "location" in data and "coordinates" in data["location"]:
            coords = data["location"]["coordinates"]

            # Check if coordinates are in GeoJSON array format [lon, lat]
            if isinstance(coords, list) and len(coords) == 2:
                # Convert back to {lat, lon} format for compatibility
                data["location"]["coordinates"] = {
                    "lon": coords[0],
                    "lat": coords[1]
                }
                logger.debug(
                    f"Converted GeoJSON [{coords[0]}, {coords[1]}] "
                    f"to {{lat: {coords[1]}, lon: {coords[0]}}}"
                )

        return data

    async def upsert_attraction(self, attraction_id: str, attraction_data: dict):
        """
        Upsert attraction.

        Args:
            attraction_id: Viator attraction ID (unique identifier)
            attraction_data: Attraction data to store
        """
        # Convert coordinates to GeoJSON format before storing
        attraction_data = self._convert_coordinates_to_geojson(attraction_data)

        result = await self.collection.update_one(
            {"attraction_id": attraction_id},
            {"$set": attraction_data},
            upsert=True
        )

        if result.upserted_id:
            logger.debug(f"Inserted new attraction: {attraction_id}")
        else:
            logger.debug(f"Updated existing attraction: {attraction_id}")

    async def get_attraction(self, attraction_id: str) -> Optional[dict]:
        """Get attraction by ID."""
        attraction = await self.collection.find_one({"attraction_id": attraction_id})
        if attraction:
            attraction = self._convert_geojson_to_coordinates(attraction)
        return attraction

    async def find_by_product_code(
        self,
        product_code: str,
        destination_id: Optional[str] = None
    ) -> Optional[dict]:
        """
        Reverse lookup: Find attraction that references this product code.

        This is the KEY method for LEVEL 2 enrichment.
        Attractions have productCodes[] array listing related activities.

        Args:
            product_code: Viator product code (e.g., "183050P6")
            destination_id: Optional destination filter for performance

        Returns:
            Attraction document with coordinates or None
        """
        query = {"productCodes": product_code}

        if destination_id:
            query["destination_id"] = destination_id

        attraction = await self.collection.find_one(query)

        if attraction:
            attraction = self._convert_geojson_to_coordinates(attraction)
            logger.debug(
                f"Found attraction for product {product_code}: "
                f"{attraction.get('name')} (ID: {attraction.get('attraction_id')})"
            )
        else:
            logger.debug(f"No attraction found for product {product_code}")

        return attraction

    async def find_by_product_codes_bulk(
        self,
        product_codes: List[str],
        destination_id: Optional[str] = None
    ) -> dict[str, dict]:
        """
        Bulk reverse lookup: Find attractions for multiple product codes.

        Args:
            product_codes: List of Viator product codes
            destination_id: Optional destination filter

        Returns:
            Dict mapping product_code → attraction document
        """
        if not product_codes:
            return {}

        query = {"productCodes": {"$in": product_codes}}

        if destination_id:
            query["destination_id"] = destination_id

        cursor = self.collection.find(query)
        attractions = await cursor.to_list(length=len(product_codes))

        # Build reverse map: productCode → attraction
        result = {}
        for attraction in attractions:
            # Convert coordinates for each attraction
            attraction = self._convert_geojson_to_coordinates(attraction)
            for product_code in attraction.get("productCodes", []):
                if product_code in product_codes:
                    result[product_code] = attraction

        logger.info(
            f"Bulk attraction lookup: {len(result)}/{len(product_codes)} products matched"
        )

        return result

    async def search_attractions(
        self,
        destination_id: str,
        limit: int = 30,
        skip: int = 0
    ) -> List[dict]:
        """
        Search attractions by destination.

        Args:
            destination_id: Viator destination ID
            limit: Maximum number of results
            skip: Number of results to skip (pagination)

        Returns:
            List of attraction documents
        """
        cursor = self.collection.find(
            {"destination_id": destination_id}
        ).skip(skip).limit(limit)

        attractions = await cursor.to_list(length=limit)
        return [self._convert_geojson_to_coordinates(a) for a in attractions]

    async def search_attractions_by_geo(
        self,
        lat: float,
        lon: float,
        radius_km: float,
        limit: int = 30
    ) -> List[dict]:
        """
        Search attractions near coordinates using geospatial query.

        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in kilometers
            limit: Maximum number of results

        Returns:
            List of attraction documents with distance
        """
        query = {
            "location.coordinates": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]  # GeoJSON: [lon, lat]
                    },
                    "$maxDistance": radius_km * 1000  # Convert to meters
                }
            }
        }

        cursor = self.collection.find(query).limit(limit)
        attractions = await cursor.to_list(length=limit)
        return [self._convert_geojson_to_coordinates(a) for a in attractions]

    async def count_attractions(self, destination_id: Optional[str] = None) -> int:
        """
        Count total attractions.

        Args:
            destination_id: Optional filter by destination

        Returns:
            Total count
        """
        query = {}
        if destination_id:
            query["destination_id"] = destination_id

        return await self.collection.count_documents(query)

    async def get_attractions_with_product_codes(
        self,
        destination_id: str,
        limit: int = 100
    ) -> List[dict]:
        """
        Get attractions that have productCodes (useful for enrichment).

        Args:
            destination_id: Viator destination ID
            limit: Maximum number of results

        Returns:
            List of attractions with productCodes
        """
        cursor = self.collection.find({
            "destination_id": destination_id,
            "productCodes": {"$exists": True, "$ne": []}
        }).limit(limit)

        attractions = await cursor.to_list(length=limit)
        return [self._convert_geojson_to_coordinates(a) for a in attractions]

    async def create_indexes(self):
        """Create MongoDB indexes for attractions collection."""
        logger.info("Creating indexes for attractions collection")

        # Attraction ID (unique)
        await self.collection.create_index("attraction_id", unique=True)

        # Destination ID (for filtering)
        await self.collection.create_index("destination_id")

        # Product codes (CRITICAL for LEVEL 2 enrichment - array index)
        await self.collection.create_index("productCodes")

        # Geospatial index for location-based queries
        await self.collection.create_index([("location.coordinates", "2dsphere")])

        # Metadata last synced
        await self.collection.create_index("metadata.last_synced")

        logger.info("Attractions indexes created successfully")
