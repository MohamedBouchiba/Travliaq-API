"""
Seed script to populate destinations collection with common cities.

This creates a minimal set of popular destinations to enable location resolution.
Run this once after deploying the Viator integration.

Usage:
    python scripts/seed_destinations.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings

# Common destinations with Viator IDs (from Viator documentation)
# These are the most popular tourist destinations
SEED_DESTINATIONS = [
    {
        "destination_id": "684",
        "name": "Paris",
        "slug": "paris",
        "country_code": "FR",
        "country_name": "France",
        "type": "city",
        "location": {
            "type": "Point",
            "coordinates": [2.3522, 48.8566]  # [lon, lat]
        },
        "timezone": "Europe/Paris",
        "metadata": {
            "is_popular": True,
            "is_seeded": True
        }
    },
    {
        "destination_id": "77",
        "name": "London",
        "slug": "london",
        "country_code": "GB",
        "country_name": "United Kingdom",
        "type": "city",
        "location": {
            "type": "Point",
            "coordinates": [-0.1276, 51.5074]
        },
        "timezone": "Europe/London",
        "metadata": {
            "is_popular": True,
            "is_seeded": True
        }
    },
    {
        "destination_id": "179",
        "name": "Rome",
        "slug": "rome",
        "country_code": "IT",
        "country_name": "Italy",
        "type": "city",
        "location": {
            "type": "Point",
            "coordinates": [12.4964, 41.9028]
        },
        "timezone": "Europe/Rome",
        "metadata": {
            "is_popular": True,
            "is_seeded": True
        }
    },
    {
        "destination_id": "706",
        "name": "Barcelona",
        "slug": "barcelona",
        "country_code": "ES",
        "country_name": "Spain",
        "type": "city",
        "location": {
            "type": "Point",
            "coordinates": [2.1734, 41.3851]
        },
        "timezone": "Europe/Madrid",
        "metadata": {
            "is_popular": True,
            "is_seeded": True
        }
    },
    {
        "destination_id": "667",
        "name": "Madrid",
        "slug": "madrid",
        "country_code": "ES",
        "country_name": "Spain",
        "type": "city",
        "location": {
            "type": "Point",
            "coordinates": [-3.7038, 40.4168]
        },
        "timezone": "Europe/Madrid",
        "metadata": {
            "is_popular": True,
            "is_seeded": True
        }
    },
    {
        "destination_id": "62",
        "name": "New York City",
        "slug": "new-york-city",
        "country_code": "US",
        "country_name": "United States",
        "type": "city",
        "location": {
            "type": "Point",
            "coordinates": [-74.0060, 40.7128]
        },
        "timezone": "America/New_York",
        "metadata": {
            "is_popular": True,
            "is_seeded": True
        }
    },
    {
        "destination_id": "24679",
        "name": "Dubai",
        "slug": "dubai",
        "country_code": "AE",
        "country_name": "United Arab Emirates",
        "type": "city",
        "location": {
            "type": "Point",
            "coordinates": [55.2708, 25.2048]
        },
        "timezone": "Asia/Dubai",
        "metadata": {
            "is_popular": True,
            "is_seeded": True
        }
    },
    {
        "destination_id": "57",
        "name": "Amsterdam",
        "slug": "amsterdam",
        "country_code": "NL",
        "country_name": "Netherlands",
        "type": "city",
        "location": {
            "type": "Point",
            "coordinates": [4.9041, 52.3676]
        },
        "timezone": "Europe/Amsterdam",
        "metadata": {
            "is_popular": True,
            "is_seeded": True
        }
    },
    {
        "destination_id": "191",
        "name": "Venice",
        "slug": "venice",
        "country_code": "IT",
        "country_name": "Italy",
        "type": "city",
        "location": {
            "type": "Point",
            "coordinates": [12.3155, 45.4408]
        },
        "timezone": "Europe/Rome",
        "metadata": {
            "is_popular": True,
            "is_seeded": True
        }
    },
    {
        "destination_id": "178",
        "name": "Florence",
        "slug": "florence",
        "country_code": "IT",
        "country_name": "Italy",
        "type": "city",
        "location": {
            "type": "Point",
            "coordinates": [11.2558, 43.7696]
        },
        "timezone": "Europe/Rome",
        "metadata": {
            "is_popular": True,
            "is_seeded": True
        }
    }
]


async def seed_destinations():
    """Seed the destinations collection with common cities."""
    settings = get_settings()

    print(f"Connecting to MongoDB: {settings.mongodb_uri}")
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db]
    collection = db[settings.mongodb_collection_destinations]

    print(f"Seeding {len(SEED_DESTINATIONS)} destinations...")

    inserted_count = 0
    updated_count = 0

    for dest in SEED_DESTINATIONS:
        result = await collection.update_one(
            {"destination_id": dest["destination_id"]},
            {"$set": dest},
            upsert=True
        )

        if result.upserted_id:
            inserted_count += 1
            print(f"  ✓ Inserted: {dest['name']} (ID: {dest['destination_id']})")
        else:
            updated_count += 1
            print(f"  ↻ Updated: {dest['name']} (ID: {dest['destination_id']})")

    print(f"\n✅ Seeding complete!")
    print(f"   Inserted: {inserted_count}")
    print(f"   Updated: {updated_count}")
    print(f"   Total: {len(SEED_DESTINATIONS)}")

    # Create indexes
    print(f"\nCreating indexes...")
    await collection.create_index("destination_id", unique=True)
    await collection.create_index("slug")
    await collection.create_index("country_code")
    await collection.create_index([("location", "2dsphere")])
    await collection.create_index([("name", "text")])
    print("✅ Indexes created")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_destinations())
