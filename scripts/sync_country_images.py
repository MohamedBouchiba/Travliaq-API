#!/usr/bin/env python3
"""
Script to synchronize images from 'countries' collection to 'country_profiles' collection.

This script dynamically fetches photo_url and photo_credit from the countries collection
(which contains images from Supabase) and updates the corresponding country_profiles.

Usage:
    python scripts/sync_country_images.py

Environment variables (from .env):
    MONGODB_URI: MongoDB connection string

No hardcoded values - all data is fetched from the database dynamically.
"""

import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient


# MongoDB Configuration
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://teamtravliaq_db_user:DUfRgh8TkEDJHSlT@travliaq-countrybasis.wljfuyy.mongodb.net/?retryWrites=true&w=majority&appName=Travliaq-CountryBasis"
)
MONGODB_DB = os.getenv("MONGODB_DB", "travliaq_knowledge_base")


async def sync_country_images():
    """
    Synchronize photo_url and photo_credit from 'countries' to 'country_profiles'.

    The 'countries' collection contains:
    - code_iso2: ISO 2-letter country code
    - photo_url: URL to country image (from Supabase or AI-generated)
    - photo_credit: Attribution for the image
    - photo_source: Source of the image

    The 'country_profiles' collection needs:
    - photo_url
    - photo_credit
    - photo_source (optional)
    """
    print(f"Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB]

    countries_collection = db.countries
    profiles_collection = db.country_profiles

    # Get all countries with images
    print(f"Fetching countries with images from 'countries' collection...")
    countries_cursor = countries_collection.find(
        {"photo_url": {"$exists": True, "$ne": None}},
        {"code_iso2": 1, "photo_url": 1, "photo_credit": 1, "photo_source": 1, "name_fr": 1}
    )
    countries_with_images = await countries_cursor.to_list(length=300)

    print(f"Found {len(countries_with_images)} countries with images")

    # Get all country profiles
    profiles_cursor = profiles_collection.find({}, {"country_code": 1, "country_name": 1, "photo_url": 1})
    profiles = await profiles_cursor.to_list(length=200)
    profiles_dict = {p["country_code"]: p for p in profiles}

    print(f"Found {len(profiles)} country profiles")

    # Track statistics
    updated = 0
    skipped = 0
    missing_profile = 0
    already_has_image = 0

    print(f"\n{'='*60}")
    print("Synchronizing images...")
    print(f"{'='*60}\n")

    for country in countries_with_images:
        code = country.get("code_iso2")
        if not code:
            continue

        photo_url = country.get("photo_url")
        photo_credit = country.get("photo_credit", "")
        photo_source = country.get("photo_source", "")
        country_name = country.get("name_fr", code)

        # Check if profile exists
        if code not in profiles_dict:
            print(f"  [{code}] {country_name}: No profile found - SKIPPING")
            missing_profile += 1
            continue

        profile = profiles_dict[code]

        # Check if profile already has an image
        existing_url = profile.get("photo_url")
        if existing_url and existing_url == photo_url:
            # Already synced
            skipped += 1
            continue

        # Update profile with image
        update_data = {
            "photo_url": photo_url,
            "updated_at": datetime.utcnow()
        }

        if photo_credit:
            update_data["photo_credit"] = photo_credit
        if photo_source:
            update_data["photo_source"] = photo_source

        result = await profiles_collection.update_one(
            {"country_code": code},
            {"$set": update_data}
        )

        if result.modified_count > 0:
            status = "UPDATED"
            if existing_url:
                status = "REPLACED"
                already_has_image += 1
            updated += 1
            print(f"  [{code}] {country_name}: {status}")
        else:
            skipped += 1

    # Find profiles without images
    print(f"\n{'='*60}")
    print("Checking for profiles without images...")
    print(f"{'='*60}\n")

    profiles_without_images = []
    for code, profile in profiles_dict.items():
        if not profile.get("photo_url"):
            profiles_without_images.append({
                "code": code,
                "name": profile.get("country_name", code)
            })

    if profiles_without_images:
        print(f"Found {len(profiles_without_images)} profiles without images:")
        for p in profiles_without_images[:20]:  # Show first 20
            print(f"  - {p['name']} ({p['code']})")
        if len(profiles_without_images) > 20:
            print(f"  ... and {len(profiles_without_images) - 20} more")
    else:
        print("All profiles have images!")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total countries with images: {len(countries_with_images)}")
    print(f"Total profiles: {len(profiles)}")
    print(f"Updated: {updated}")
    print(f"Already synced: {skipped}")
    print(f"Missing profiles: {missing_profile}")
    print(f"Profiles without images: {len(profiles_without_images)}")

    client.close()
    print("\nDone!")

    return {
        "updated": updated,
        "skipped": skipped,
        "missing_profile": missing_profile,
        "profiles_without_images": len(profiles_without_images)
    }


async def list_profiles_without_images():
    """List all country profiles that don't have a photo_url."""
    print(f"Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB]

    profiles_collection = db.country_profiles

    # Find profiles without photo_url
    cursor = profiles_collection.find(
        {"$or": [
            {"photo_url": {"$exists": False}},
            {"photo_url": None},
            {"photo_url": ""}
        ]},
        {"country_code": 1, "country_name": 1, "region": 1}
    )

    profiles = await cursor.to_list(length=200)

    print(f"\nProfiles without images ({len(profiles)}):")
    print(f"{'='*60}")

    by_region = {}
    for p in profiles:
        region = p.get("region", "Unknown")
        if region not in by_region:
            by_region[region] = []
        by_region[region].append(p)

    for region, countries in sorted(by_region.items()):
        print(f"\n{region} ({len(countries)}):")
        for c in countries:
            print(f"  - {c.get('country_name', 'Unknown')} ({c.get('country_code', '??')})")

    client.close()
    return profiles


if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Run sync
    asyncio.run(sync_country_images())
