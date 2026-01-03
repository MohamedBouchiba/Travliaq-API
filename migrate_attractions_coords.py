"""
Migration script to convert existing attractions coordinates from {lat, lon} to GeoJSON format.

This fixes the MongoDB 2dsphere index error:
"Can't extract geo keys... can't project geometry into spherical CRS"
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL")

async def migrate_attractions():
    """Migrate all attractions coordinates to GeoJSON format."""

    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.travliaq
    collection = db.attractions

    logger.info("Starting attractions coordinates migration...")

    # Find all attractions with {lat, lon} format coordinates
    query = {
        "location.coordinates.lat": {"$exists": True},
        "location.coordinates.lon": {"$exists": True}
    }

    cursor = collection.find(query)
    attractions = await cursor.to_list(length=None)

    logger.info(f"Found {len(attractions)} attractions with old coordinate format")

    converted = 0
    errors = 0

    for attraction in attractions:
        try:
            attraction_id = attraction.get("attraction_id") or attraction.get("product_code")
            coords = attraction["location"]["coordinates"]

            if isinstance(coords, dict) and "lat" in coords and "lon" in coords:
                lat = coords["lat"]
                lon = coords["lon"]

                # Convert to GeoJSON: [longitude, latitude]
                new_coords = [lon, lat]

                # Update in database
                result = await collection.update_one(
                    {"_id": attraction["_id"]},
                    {"$set": {"location.coordinates": new_coords}}
                )

                if result.modified_count > 0:
                    converted += 1
                    logger.info(
                        f"✓ Converted {attraction_id}: "
                        f"{{lat: {lat}, lon: {lon}}} → [{lon}, {lat}]"
                    )
                else:
                    logger.warning(f"⚠️  No change for {attraction_id}")

        except Exception as e:
            errors += 1
            logger.error(f"✗ Error converting {attraction_id}: {e}")

    logger.info("="*80)
    logger.info("Migration Complete:")
    logger.info(f"  Converted: {converted}")
    logger.info(f"  Errors: {errors}")
    logger.info(f"  Total: {len(attractions)}")
    logger.info("="*80)

    # Verify: Count attractions with GeoJSON format
    geojson_count = await collection.count_documents({
        "location.coordinates.0": {"$exists": True}  # GeoJSON format is an array
    })

    logger.info(f"Attractions with GeoJSON coordinates: {geojson_count}")

    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_attractions())
