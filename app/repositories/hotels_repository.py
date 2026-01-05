"""MongoDB repository for hotels data caching.

This repository caches Booking.com API data to minimize API costs:
- Destination mappings (city -> dest_id) - permanent
- Hotel static data (name, coords, stars, photos, amenities) - 90 days TTL
- Price history for indicative pricing - 30 days TTL
"""

from __future__ import annotations
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ReturnDocument

logger = logging.getLogger(__name__)


class HotelsRepository:
    """Repository for hotels-related collections in MongoDB."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        destinations_collection_name: str = "booking_destinations",
        hotels_collection_name: str = "hotels_static"
    ):
        self.db = db
        self.destinations: AsyncIOMotorCollection = db[destinations_collection_name]
        self.hotels: AsyncIOMotorCollection = db[hotels_collection_name]

    # =========================================================================
    # DESTINATION MAPPINGS (city -> dest_id, dest_type)
    # =========================================================================

    @staticmethod
    def _destination_key(city: str, country_code: str) -> str:
        """Generate unique key for destination."""
        normalized = f"{city.lower().strip()}:{country_code.upper().strip()}"
        return hashlib.md5(normalized.encode()).hexdigest()

    async def get_destination(
        self,
        city: str,
        country_code: str
    ) -> Optional[Tuple[str, str]]:
        """
        Get cached destination mapping.

        Args:
            city: City name
            country_code: ISO country code

        Returns:
            Tuple of (dest_id, dest_type) or None if not cached
        """
        dest_key = self._destination_key(city, country_code)

        result = await self.destinations.find_one_and_update(
            {"dest_key": dest_key},
            {
                "$set": {"last_used": datetime.utcnow()},
                "$inc": {"use_count": 1}
            },
            return_document=ReturnDocument.AFTER
        )

        if result:
            logger.debug(
                f"Destination cache HIT: {city}, {country_code} "
                f"-> {result['dest_id']} ({result['dest_type']})"
            )
            return result["dest_id"], result["dest_type"]

        logger.debug(f"Destination cache MISS: {city}, {country_code}")
        return None

    async def save_destination(
        self,
        city: str,
        country_code: str,
        dest_id: str,
        dest_type: str
    ):
        """
        Cache destination mapping (permanent).

        Args:
            city: City name
            country_code: ISO country code
            dest_id: Booking.com destination ID
            dest_type: Destination type (city, region, etc.)
        """
        dest_key = self._destination_key(city, country_code)

        await self.destinations.update_one(
            {"dest_key": dest_key},
            {
                "$set": {
                    "dest_key": dest_key,
                    "city": city,
                    "country_code": country_code.upper(),
                    "dest_id": dest_id,
                    "dest_type": dest_type,
                    "created_at": datetime.utcnow(),
                    "last_used": datetime.utcnow(),
                    "use_count": 1
                }
            },
            upsert=True
        )

        logger.info(f"Destination cached: {city}, {country_code} -> {dest_id} ({dest_type})")

    # =========================================================================
    # HOTEL STATIC DATA
    # =========================================================================

    async def get_hotel_static(self, hotel_id: str) -> Optional[dict]:
        """
        Get cached static hotel data.

        Args:
            hotel_id: Hotel ID (with or without htl_ prefix)

        Returns:
            Dict with static hotel data or None if not cached
        """
        raw_id = hotel_id.replace("htl_", "")

        result = await self.hotels.find_one_and_update(
            {"hotel_id": raw_id},
            {
                "$set": {"last_accessed": datetime.utcnow()},
                "$inc": {"access_count": 1}
            },
            return_document=ReturnDocument.AFTER
        )

        if result:
            logger.debug(f"Hotel static cache HIT: {hotel_id}")
            return result.get("data")

        logger.debug(f"Hotel static cache MISS: {hotel_id}")
        return None

    async def save_hotel_static(
        self,
        hotel_id: str,
        data: dict,
        city: Optional[str] = None,
        country_code: Optional[str] = None
    ):
        """
        Cache static hotel data.

        Static data includes: name, coordinates, stars, address, photos, amenities.
        Does NOT include: prices, availability, rooms.

        Args:
            hotel_id: Hotel ID
            data: Static hotel data
            city: City name (for city-based queries)
            country_code: Country code
        """
        raw_id = hotel_id.replace("htl_", "")

        doc = {
            "hotel_id": raw_id,
            "data": data,
            "last_updated": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "access_count": 1
        }

        if city:
            doc["city"] = city.lower()
        if country_code:
            doc["country_code"] = country_code.upper()

        await self.hotels.update_one(
            {"hotel_id": raw_id},
            {"$set": doc},
            upsert=True
        )

        logger.info(f"Hotel static cached: {hotel_id}")

    async def get_hotels_by_city(
        self,
        city: str,
        country_code: str,
        limit: int = 50
    ) -> List[dict]:
        """
        Get cached hotels for a city.

        Args:
            city: City name
            country_code: Country code
            limit: Max results

        Returns:
            List of hotel static data
        """
        cursor = self.hotels.find(
            {
                "city": city.lower(),
                "country_code": country_code.upper()
            }
        ).limit(limit)

        results = await cursor.to_list(length=limit)
        logger.debug(f"Found {len(results)} cached hotels for {city}, {country_code}")

        return [r.get("data") for r in results if r.get("data")]

    async def save_hotels_batch(
        self,
        hotels: List[dict],
        city: str,
        country_code: str
    ):
        """
        Batch save hotels for a city.

        Args:
            hotels: List of hotel data dicts
            city: City name
            country_code: Country code
        """
        if not hotels:
            return

        from pymongo import UpdateOne

        operations = []
        for hotel in hotels:
            hotel_id = hotel.get("id", "").replace("htl_", "")
            if not hotel_id:
                continue

            # Extract static data only
            static_data = {
                "id": hotel.get("id"),
                "name": hotel.get("name"),
                "lat": hotel.get("lat"),
                "lng": hotel.get("lng"),
                "stars": hotel.get("stars"),
                "address": hotel.get("address"),
                "imageUrl": hotel.get("imageUrl"),
                "amenities": hotel.get("amenities", []),
                "rating": hotel.get("rating"),
                "reviewCount": hotel.get("reviewCount"),
                "distanceFromCenter": hotel.get("distanceFromCenter")
            }

            operations.append(UpdateOne(
                {"hotel_id": hotel_id},
                {
                    "$set": {
                        "hotel_id": hotel_id,
                        "data": static_data,
                        "city": city.lower(),
                        "country_code": country_code.upper(),
                        "last_updated": datetime.utcnow(),
                        "last_accessed": datetime.utcnow()
                    },
                    "$setOnInsert": {"access_count": 1}
                },
                upsert=True
            ))

        if operations:
            result = await self.hotels.bulk_write(operations)
            logger.info(
                f"Batch saved {result.upserted_count + result.modified_count} "
                f"hotels for {city}, {country_code}"
            )

    # =========================================================================
    # PRICE HISTORY (for indicative pricing without API calls)
    # =========================================================================

    async def save_price_history(
        self,
        hotel_id: str,
        price_per_night: float,
        currency: str
    ):
        """
        Save price to history for indicative pricing.

        Args:
            hotel_id: Hotel ID
            price_per_night: Price per night
            currency: Currency code
        """
        raw_id = hotel_id.replace("htl_", "")

        await self.hotels.update_one(
            {"hotel_id": raw_id},
            {
                "$push": {
                    "price_history": {
                        "$each": [{
                            "price": price_per_night,
                            "currency": currency,
                            "date": datetime.utcnow()
                        }],
                        "$slice": -10  # Keep last 10 prices
                    }
                },
                "$set": {
                    "last_known_price": price_per_night,
                    "last_price_currency": currency,
                    "last_price_date": datetime.utcnow()
                }
            }
        )

    async def get_indicative_price(
        self,
        hotel_id: str
    ) -> Optional[Tuple[float, str]]:
        """
        Get last known price for indicative display.

        Args:
            hotel_id: Hotel ID

        Returns:
            Tuple of (price, currency) or None
        """
        raw_id = hotel_id.replace("htl_", "")

        result = await self.hotels.find_one(
            {"hotel_id": raw_id},
            {"last_known_price": 1, "last_price_currency": 1, "last_price_date": 1}
        )

        if result and result.get("last_known_price"):
            # Only return if price is less than 30 days old
            price_date = result.get("last_price_date")
            if price_date and (datetime.utcnow() - price_date) < timedelta(days=30):
                return result["last_known_price"], result.get("last_price_currency", "EUR")

        return None

    async def get_city_indicative_price(
        self,
        city: str,
        country_code: str
    ) -> Optional[Tuple[float, str]]:
        """
        Get minimum indicative price for a city (for map-prices without API call).

        Args:
            city: City name
            country_code: Country code

        Returns:
            Tuple of (min_price, currency) or None
        """
        cutoff = datetime.utcnow() - timedelta(days=30)

        pipeline = [
            {
                "$match": {
                    "city": city.lower(),
                    "country_code": country_code.upper(),
                    "last_price_date": {"$gte": cutoff},
                    "last_known_price": {"$gt": 0}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "min_price": {"$min": "$last_known_price"},
                    "currency": {"$first": "$last_price_currency"}
                }
            }
        ]

        result = await self.hotels.aggregate(pipeline).to_list(length=1)

        if result:
            return result[0]["min_price"], result[0].get("currency", "EUR")

        return None

    # =========================================================================
    # INDEX MANAGEMENT
    # =========================================================================

    async def create_indexes(self):
        """Create MongoDB indexes for hotels collections."""
        logger.info("Creating indexes for hotels collections")

        # Destinations indexes
        await self.destinations.create_index("dest_key", unique=True)
        await self.destinations.create_index([("city", 1), ("country_code", 1)])

        # Hotels static indexes
        await self.hotels.create_index("hotel_id", unique=True)
        await self.hotels.create_index([("city", 1), ("country_code", 1)])
        await self.hotels.create_index("last_updated")
        await self.hotels.create_index("last_price_date")

        # TTL index for auto-cleanup (90 days without access)
        try:
            await self.hotels.create_index(
                "last_accessed",
                name="last_accessed_ttl",
                expireAfterSeconds=90 * 24 * 60 * 60  # 90 days
            )
        except Exception as e:
            if "IndexOptionsConflict" in str(e) or "already exists" in str(e):
                logger.warning(f"TTL index already exists: {e}")
            else:
                raise

        logger.info("Hotels indexes created successfully")

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        dest_count = await self.destinations.count_documents({})
        hotel_count = await self.hotels.count_documents({})

        # Count hotels with recent prices
        cutoff = datetime.utcnow() - timedelta(days=30)
        hotels_with_prices = await self.hotels.count_documents({
            "last_price_date": {"$gte": cutoff}
        })

        return {
            "destinations_cached": dest_count,
            "hotels_cached": hotel_count,
            "hotels_with_recent_prices": hotels_with_prices
        }
