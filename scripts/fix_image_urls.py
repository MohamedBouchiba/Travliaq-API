#!/usr/bin/env python3
"""
Script to fix image URLs in MongoDB.

Problem: Some countries have local file paths instead of Supabase URLs.
Solution: Convert local paths to Supabase public URLs.

Local path format: /home/.../generated_images/XX_CountryName_ai_generated.png
Supabase URL format: https://cinbnmlfpffmyjmkwbco.supabase.co/storage/v1/object/public/Country/XX_ai_generated.png

Usage:
    python scripts/fix_image_urls.py
"""

import asyncio
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient


# Supabase configuration
SUPABASE_URL = "https://cinbnmlfpffmyjmkwbco.supabase.co"
SUPABASE_BUCKET = "Country"

# MongoDB Configuration
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://teamtravliaq_db_user:DUfRgh8TkEDJHSlT@travliaq-countrybasis.wljfuyy.mongodb.net/?retryWrites=true&w=majority&appName=Travliaq-CountryBasis"
)
MONGODB_DB = os.getenv("MONGODB_DB", "travliaq_knowledge_base")


def convert_local_to_supabase_url(local_path: str) -> str:
    """
    Convert a local file path to Supabase public URL.

    Input: /home/.../generated_images/XX_CountryName_ai_generated.png
    Output: https://cinbnmlfpffmyjmkwbco.supabase.co/storage/v1/object/public/Country/XX_ai_generated.png
    """
    # Extract country code from filename
    # Pattern: XX_something_ai_generated.png
    filename = os.path.basename(local_path)

    # Extract country code (first 2-3 characters before underscore)
    match = re.match(r'^([A-Z]{2,3})_', filename)
    if not match:
        return None

    country_code = match.group(1)

    # Build Supabase URL
    supabase_filename = f"{country_code}_ai_generated.png"
    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{supabase_filename}"


async def fix_image_urls():
    """Fix all local file paths to Supabase URLs."""
    print(f"Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB]

    # Collections to update
    collections = [
        ("country_profiles", "country_code", "photo_url"),
        ("countries", "code_iso2", "photo_url"),
    ]

    total_fixed = 0

    for collection_name, code_field, url_field in collections:
        collection = db[collection_name]

        # Find documents with local paths
        local_docs = await collection.find({
            url_field: {"$regex": "^/home/", "$options": "i"}
        }).to_list(500)

        print(f"\n{'='*60}")
        print(f"Collection: {collection_name}")
        print(f"Documents with local paths: {len(local_docs)}")
        print(f"{'='*60}")

        if not local_docs:
            print("  No local paths to fix!")
            continue

        fixed = 0
        errors = 0

        for doc in local_docs:
            code = doc.get(code_field, "??")
            local_path = doc.get(url_field)

            # Convert to Supabase URL
            supabase_url = convert_local_to_supabase_url(local_path)

            if not supabase_url:
                print(f"  [{code}] Could not parse: {local_path}")
                errors += 1
                continue

            # Update document
            result = await collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    url_field: supabase_url,
                    "updated_at": datetime.utcnow()
                }}
            )

            if result.modified_count > 0:
                print(f"  [{code}] Fixed: {supabase_url}")
                fixed += 1
            else:
                print(f"  [{code}] No change")

        print(f"\n  Summary: {fixed} fixed, {errors} errors")
        total_fixed += fixed

    client.close()

    print(f"\n{'='*60}")
    print(f"TOTAL FIXED: {total_fixed}")
    print(f"{'='*60}")

    return total_fixed


async def verify_urls():
    """Verify all URLs are now Supabase URLs."""
    print(f"\nVerifying URLs...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB]

    # Check country_profiles
    local_profiles = await db.country_profiles.count_documents({
        "photo_url": {"$regex": "^/home/", "$options": "i"}
    })

    supabase_profiles = await db.country_profiles.count_documents({
        "photo_url": {"$regex": "^https://.*supabase", "$options": "i"}
    })

    total_profiles = await db.country_profiles.count_documents({})

    print(f"\nCountry Profiles:")
    print(f"  Total: {total_profiles}")
    print(f"  Supabase URLs: {supabase_profiles}")
    print(f"  Local paths remaining: {local_profiles}")

    # Sample some fixed URLs
    sample = await db.country_profiles.find(
        {"photo_url": {"$regex": "^https://.*supabase"}},
        {"country_code": 1, "photo_url": 1}
    ).limit(5).to_list(5)

    print(f"\nSample fixed URLs:")
    for s in sample:
        print(f"  {s.get('country_code')}: {s.get('photo_url')[:70]}...")

    client.close()


if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Run fix
    asyncio.run(fix_image_urls())

    # Verify
    asyncio.run(verify_urls())
