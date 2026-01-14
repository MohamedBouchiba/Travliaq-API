#!/usr/bin/env python3
"""
Update all country profile images:
1. Use chosen URLs from image_choices.json for countries with image_1/image_2 choice
2. Use Supabase URLs for countries with "none" choice (AI-generated images)
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB Configuration
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://teamtravliaq_db_user:DUfRgh8TkEDJHSlT@travliaq-countrybasis.wljfuyy.mongodb.net/?retryWrites=true&w=majority&appName=Travliaq-CountryBasis"
)
MONGODB_DB = os.getenv("MONGODB_DB", "travliaq_knowledge_base")

# Supabase configuration for AI-generated images
SUPABASE_BASE_URL = "https://cinbnmlfpffmyjmkwbco.supabase.co/storage/v1/object/public/Country/img"


def load_image_choices():
    """Load image choices from JSON file."""
    choices_file = Path("/home/mohamed-bouchiba/Bureau/Travliaq/image_choices.json")
    with open(choices_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_image_url(code: str, data: dict) -> tuple[str, str]:
    """
    Get the image URL for a country.
    Returns (url, source) where source is 'unsplash' or 'supabase'
    """
    choice = data.get("choice", "none")
    country_name = data.get("country_name", code)

    if choice == "image_1":
        return data.get("photo_url_1"), "unsplash"
    elif choice == "image_2":
        return data.get("photo_url_2"), "unsplash"
    else:
        # Use Supabase URL for AI-generated image
        # Format: img/XX_CountryName.png
        safe_name = country_name.replace(" ", "_").replace("'", "").replace(",", "")
        supabase_url = f"{SUPABASE_BASE_URL}/{code}_{safe_name}.png"
        return supabase_url, "supabase"


async def update_country_images():
    """Update all country profile images."""
    print("Loading image choices...")
    choices = load_image_choices()
    print(f"Loaded {len(choices)} country image choices")

    print(f"\nConnecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB]
    collection = db.country_profiles

    # Get all existing profiles
    profiles = await collection.find({}, {"country_code": 1, "country_name": 1}).to_list(200)
    profile_codes = {p["country_code"] for p in profiles}
    print(f"Found {len(profiles)} existing country profiles")

    # Statistics
    updated_unsplash = 0
    updated_supabase = 0
    not_in_db = 0
    errors = 0

    print(f"\n{'='*60}")
    print("Updating country images...")
    print(f"{'='*60}\n")

    for code, data in sorted(choices.items()):
        country_name = data.get("country_name", code)

        # Check if country exists in our profiles
        if code not in profile_codes:
            # Skip countries not in our database
            continue

        url, source = get_image_url(code, data)

        if not url:
            print(f"  [{code}] {country_name}: No URL found - SKIPPING")
            errors += 1
            continue

        # Update the profile
        result = await collection.update_one(
            {"country_code": code},
            {"$set": {
                "photo_url": url,
                "photo_source": source,
                "updated_at": datetime.utcnow()
            }}
        )

        if result.modified_count > 0:
            if source == "unsplash":
                updated_unsplash += 1
                print(f"  [{code}] {country_name}: Unsplash URL")
            else:
                updated_supabase += 1
                print(f"  [{code}] {country_name}: Supabase AI image")
        else:
            # Maybe already up to date
            pass

    client.close()

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Updated with Unsplash URLs: {updated_unsplash}")
    print(f"Updated with Supabase URLs: {updated_supabase}")
    print(f"Total updated: {updated_unsplash + updated_supabase}")
    print(f"Errors: {errors}")

    return {
        "unsplash": updated_unsplash,
        "supabase": updated_supabase,
        "errors": errors
    }


if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    asyncio.run(update_country_images())
