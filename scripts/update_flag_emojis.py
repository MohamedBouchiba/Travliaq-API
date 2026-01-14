#!/usr/bin/env python3
"""
Update flag_emoji field in country_profiles to use actual emoji flags.

Converts ISO2 country codes to regional indicator symbols (flag emojis).
Example: FR -> 🇫🇷, ES -> 🇪🇸, JP -> 🇯🇵
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB Configuration
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://teamtravliaq_db_user:DUfRgh8TkEDJHSlT@travliaq-countrybasis.wljfuyy.mongodb.net/?retryWrites=true&w=majority&appName=Travliaq-CountryBasis"
)
MONGODB_DB = os.getenv("MONGODB_DB", "travliaq_knowledge_base")


def country_code_to_flag_emoji(country_code: str) -> str:
    """
    Convert ISO2 country code to flag emoji using regional indicator symbols.

    Each letter is converted to its regional indicator symbol:
    A -> 🇦 (U+1F1E6), B -> 🇧 (U+1F1E7), etc.

    Example: FR -> 🇫🇷, US -> 🇺🇸, JP -> 🇯🇵
    """
    if not country_code or len(country_code) != 2:
        return ""

    # Regional indicator symbols start at U+1F1E6 for 'A'
    REGIONAL_INDICATOR_A = 0x1F1E6

    code = country_code.upper()
    flag = ""
    for char in code:
        if 'A' <= char <= 'Z':
            # Convert letter to regional indicator symbol
            flag += chr(REGIONAL_INDICATOR_A + ord(char) - ord('A'))

    return flag


async def update_flag_emojis():
    """Update all country profiles with proper flag emojis."""
    print("Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB]
    collection = db.country_profiles

    # Get all profiles
    profiles = await collection.find({}, {"country_code": 1, "country_name": 1, "flag_emoji": 1}).to_list(200)
    print(f"Found {len(profiles)} country profiles")

    updated = 0
    already_emoji = 0

    print(f"\n{'='*60}")
    print("Updating flag emojis...")
    print(f"{'='*60}\n")

    for profile in profiles:
        country_code = profile.get("country_code", "")
        country_name = profile.get("country_name", country_code)
        current_flag = profile.get("flag_emoji", "")

        # Generate proper flag emoji
        flag_emoji = country_code_to_flag_emoji(country_code)

        if not flag_emoji:
            print(f"  [{country_code}] {country_name}: Could not generate flag emoji")
            continue

        # Check if already an emoji (starts with regional indicator)
        if current_flag and ord(current_flag[0]) >= 0x1F1E6:
            already_emoji += 1
            continue

        # Update the profile
        result = await collection.update_one(
            {"_id": profile["_id"]},
            {"$set": {
                "flag_emoji": flag_emoji,
                "updated_at": datetime.now(timezone.utc)
            }}
        )

        if result.modified_count > 0:
            print(f"  [{country_code}] {country_name}: {flag_emoji}")
            updated += 1

    client.close()

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Updated: {updated}")
    print(f"Already had emoji: {already_emoji}")
    print(f"Total: {len(profiles)}")

    return {"updated": updated, "already_emoji": already_emoji}


async def verify_flags():
    """Verify all flags are now emojis."""
    print("\nVerifying flag emojis...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB]

    # Get sample of profiles
    samples = await db.country_profiles.find(
        {},
        {"country_code": 1, "country_name": 1, "flag_emoji": 1}
    ).limit(15).to_list(15)

    print(f"\nSample flags:")
    for s in samples:
        print(f"  {s.get('flag_emoji', '?')} {s.get('country_name')} ({s.get('country_code')})")

    client.close()


if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Run update
    asyncio.run(update_flag_emojis())

    # Verify
    asyncio.run(verify_flags())
