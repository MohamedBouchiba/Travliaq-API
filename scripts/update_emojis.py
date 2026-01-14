#!/usr/bin/env python3
"""
Script to update emoji codes to Unicode characters in country profiles.

This script connects to MongoDB and updates all emoji fields from text codes
(like "beach", "wine_glass") to actual Unicode emoji characters.

Usage:
    python scripts/update_emojis.py

Environment variables:
    MONGODB_URI: MongoDB connection string
    MONGODB_DB: Database name
"""

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient

# Mapping of text codes to Unicode emoji characters
EMOJI_MAPPING = {
    # Landmarks & Buildings
    "fr": "🗼",
    "classical_building": "🏛️",
    "european_castle": "🏰",
    "church": "⛪",
    "mosque": "🕌",
    "moyai": "🗿",
    "statue_of_liberty": "🗽",
    "tokyo_tower": "🗼",
    "temple": "🛕",
    "shinto_shrine": "⛩️",
    "synagogue": "🕍",
    "kaaba": "🕋",

    # Nature & Geography
    "mountain": "🏔️",
    "volcano": "🌋",
    "beach": "🏖️",
    "desert": "🏜️",
    "island": "🏝️",
    "evergreen_tree": "🌲",
    "palm_tree": "🌴",
    "fallen_leaf": "🍂",
    "sunrise": "🌅",
    "sunset": "🌇",
    "rainbow": "🌈",
    "ocean": "🌊",
    "snowflake": "❄️",
    "cactus": "🌵",
    "tulip": "🌷",
    "flower": "🌸",
    "hibiscus": "🌺",
    "sunflower": "🌻",
    "blossom": "🌼",
    "rose": "🌹",

    # Animals & Wildlife
    "elephant": "🐘",
    "lion": "🦁",
    "tiger": "🐅",
    "zebra": "🦓",
    "giraffe": "🦒",
    "monkey": "🐒",
    "gorilla": "🦍",
    "koala": "🐨",
    "kangaroo": "🦘",
    "panda": "🐼",
    "bear": "🐻",
    "penguin": "🐧",
    "whale": "🐋",
    "dolphin": "🐬",
    "fish": "🐟",
    "tropical_fish": "🐠",
    "turtle": "🐢",
    "crocodile": "🐊",
    "snake": "🐍",
    "dragon": "🐉",
    "camel": "🐫",
    "llama": "🦙",
    "flamingo": "🦩",
    "peacock": "🦚",
    "parrot": "🦜",
    "eagle": "🦅",
    "owl": "🦉",
    "butterfly": "🦋",

    # Food & Drinks
    "wine_glass": "🍷",
    "beer": "🍺",
    "cocktail": "🍸",
    "coffee": "☕",
    "tea": "🍵",
    "sake": "🍶",
    "pizza": "🍕",
    "hamburger": "🍔",
    "taco": "🌮",
    "burrito": "🌯",
    "sushi": "🍣",
    "ramen": "🍜",
    "rice": "🍚",
    "curry": "🍛",
    "spaghetti": "🍝",
    "bread": "🍞",
    "croissant": "🥐",
    "baguette": "🥖",
    "cheese": "🧀",
    "meat": "🥩",
    "poultry": "🍗",
    "shrimp": "🦐",
    "crab": "🦀",
    "lobster": "🦞",
    "oyster": "🦪",
    "ice_cream": "🍨",
    "cake": "🍰",
    "cookie": "🍪",
    "chocolate": "🍫",
    "candy": "🍬",
    "doughnut": "🍩",
    "apple": "🍎",
    "grapes": "🍇",
    "watermelon": "🍉",
    "pineapple": "🍍",
    "mango": "🥭",
    "coconut": "🥥",
    "avocado": "🥑",
    "hot_pepper": "🌶️",
    "corn": "🌽",
    "plate_with_cutlery": "🍽️",
    "fork_and_knife": "🍴",

    # Activities & Sports
    "ski": "⛷️",
    "snowboard": "🏂",
    "surfing": "🏄",
    "swimming": "🏊",
    "diving": "🤿",
    "kayak": "🛶",
    "bike": "🚴",
    "hiking": "🥾",
    "climbing": "🧗",
    "golf": "⛳",
    "tennis": "🎾",
    "soccer": "⚽",
    "basketball": "🏀",
    "volleyball": "🏐",
    "cricket": "🏏",
    "rugby": "🏉",
    "yoga": "🧘",
    "meditation": "🧘",
    "spa": "💆",
    "massage": "💆",

    # Transport
    "boat": "🚣",
    "sailboat": "⛵",
    "ship": "🚢",
    "yacht": "🛥️",
    "canoe": "🛶",
    "airplane": "✈️",
    "helicopter": "🚁",
    "train": "🚂",
    "tram": "🚋",
    "bus": "🚌",
    "car": "🚗",
    "motorcycle": "🏍️",
    "bicycle": "🚲",
    "rickshaw": "🛺",
    "cable_car": "🚡",

    # Culture & Entertainment
    "art": "🎨",
    "palette": "🎨",
    "musical_note": "🎵",
    "guitar": "🎸",
    "violin": "🎻",
    "drum": "🥁",
    "microphone": "🎤",
    "headphones": "🎧",
    "theater": "🎭",
    "movie": "🎬",
    "camera": "📷",
    "book": "📚",
    "scroll": "📜",
    "dancer": "💃",
    "flamenco": "💃",
    "ballet": "🩰",
    "mask": "🎭",
    "fireworks": "🎆",
    "sparkler": "🎇",
    "balloon": "🎈",
    "party": "🎉",
    "confetti": "🎊",
    "gift": "🎁",
    "ribbon": "🎀",
    "trophy": "🏆",
    "medal": "🏅",
    "crown": "👑",

    # Night & Sky
    "night_with_stars": "🌃",
    "moon": "🌙",
    "stars": "⭐",
    "milky_way": "🌌",
    "star": "⭐",
    "shooting_star": "🌠",
    "sparkles": "✨",
    "comet": "☄️",
    "sun": "☀️",
    "cloud": "☁️",
    "rainbow": "🌈",

    # Misc
    "heart": "❤️",
    "gem": "💎",
    "money": "💰",
    "shopping": "🛍️",
    "shopping_bags": "🛍️",
    "compass": "🧭",
    "map": "🗺️",
    "globe": "🌍",
    "hot_springs": "♨️",
    "camping": "🏕️",
    "tent": "⛺",
    "house": "🏠",
    "hut": "🛖",
    "mosque_emoji": "🕌",
    "temple_emoji": "🛕",
    "pagoda": "🏯",
    "ferris_wheel": "🎡",
    "roller_coaster": "🎢",
    "carousel": "🎠",

    # Flags (country codes)
    "JP": "🇯🇵",
    "TH": "🇹🇭",
    "VN": "🇻🇳",
    "ID": "🇮🇩",
    "MY": "🇲🇾",
    "SG": "🇸🇬",
    "PH": "🇵🇭",
    "KR": "🇰🇷",
    "CN": "🇨🇳",
    "IN": "🇮🇳",
    "NP": "🇳🇵",
    "LK": "🇱🇰",
    "MV": "🇲🇻",
}

# Default emoji if code not found
DEFAULT_EMOJI = "✨"


async def update_emojis():
    """Update all emoji fields in country profiles from text codes to Unicode."""
    # Get MongoDB connection settings
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_db = os.getenv("MONGODB_DB", "travliaq")
    collection_name = os.getenv("MONGODB_COLLECTION_COUNTRY_PROFILES", "country_profiles")

    print(f"Connecting to MongoDB: {mongodb_db}/{collection_name}")

    client = AsyncIOMotorClient(mongodb_uri)
    db = client[mongodb_db]
    collection = db[collection_name]

    # Get all profiles
    cursor = collection.find({})
    profiles = await cursor.to_list(length=None)

    print(f"Found {len(profiles)} country profiles")

    updated_count = 0

    for profile in profiles:
        country_code = profile.get("country_code", "??")
        top_activities = profile.get("top_activities", [])

        if not top_activities:
            continue

        needs_update = False
        updated_activities = []

        for activity in top_activities:
            emoji_code = activity.get("emoji", "")

            # Check if already a Unicode emoji (length 1-2 for most emojis)
            if len(emoji_code) <= 4 and not emoji_code.isalnum():
                # Already Unicode emoji
                updated_activities.append(activity)
                continue

            # Convert from text code to Unicode
            new_emoji = EMOJI_MAPPING.get(emoji_code, DEFAULT_EMOJI)

            if new_emoji != emoji_code:
                needs_update = True
                print(f"  {country_code}: '{activity.get('name')}' - '{emoji_code}' -> '{new_emoji}'")

            updated_activities.append({
                **activity,
                "emoji": new_emoji
            })

        if needs_update:
            # Update the document
            await collection.update_one(
                {"_id": profile["_id"]},
                {"$set": {"top_activities": updated_activities}}
            )
            updated_count += 1

    print(f"\nUpdated {updated_count} country profiles")

    # Close connection
    client.close()


if __name__ == "__main__":
    asyncio.run(update_emojis())
