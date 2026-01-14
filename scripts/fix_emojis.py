#!/usr/bin/env python3
"""
Script to fix emoji text names to Unicode emojis in country_profiles.

Reads all country_profiles from MongoDB and replaces text emoji names
(like "beach", "church") with actual Unicode emojis.

Usage:
    python scripts/fix_emojis.py
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://teamtravliaq_db_user:DUfRgh8TkEDJHSlT@travliaq-countrybasis.wljfuyy.mongodb.net/?retryWrites=true&w=majority&appName=Travliaq-CountryBasis"
)
MONGODB_DB = os.getenv("MONGODB_DB", "travliaq_knowledge_base")

# ============================================================================
# EMOJI MAPPING - Text names to Unicode
# ============================================================================

EMOJI_FIX_MAP = {
    # Buildings & Monuments
    "church": "⛪",
    "mosque": "🕌",
    "classical_building": "🏛️",
    "european_castle": "🏰",
    "japanese_castle": "🏯",
    "statue_of_liberty": "🗽",
    "tokyo_tower": "🗼",
    "shinto_shrine": "⛩️",
    "kaaba": "🕋",
    "synagogue": "🕍",
    "hindu_temple": "🛕",
    "pagoda": "🛖",

    # Nature & Landscapes
    "beach": "🏖️",
    "beach_with_umbrella": "🏖️",
    "mountain": "⛰️",
    "mount_fuji": "🗻",
    "desert": "🏜️",
    "desert_island": "🏝️",
    "palm_tree": "🌴",
    "deciduous_tree": "🌳",
    "evergreen_tree": "🌲",
    "national_park": "🏞️",
    "sunrise_over_mountains": "🌄",
    "sunrise": "🌅",
    "sunset": "🌇",
    "night_with_stars": "🌃",
    "milky_way": "🌌",
    "volcano": "🌋",
    "waterfall": "💧",
    "ocean": "🌊",
    "wave": "🌊",
    "coral": "🪸",
    "cactus": "🌵",
    "bamboo": "🎋",
    "cherry_blossom": "🌸",
    "tulip": "🌷",
    "sunflower": "🌻",
    "hibiscus": "🌺",

    # Transport
    "boat": "🚣",
    "sailboat": "⛵",
    "ship": "🚢",
    "ferry": "⛴️",
    "canoe": "🛶",
    "tram": "🚃",
    "train": "🚆",
    "steam_locomotive": "🚂",
    "bullet_train": "🚄",
    "metro": "🚇",
    "airplane": "✈️",
    "helicopter": "🚁",
    "cable_car": "🚡",
    "bus": "🚌",
    "taxi": "🚕",
    "rickshaw": "🛺",
    "bike": "🚲",
    "scooter": "🛵",

    # Food & Drinks
    "plate_with_cutlery": "🍽️",
    "fork_and_knife": "🍴",
    "wine_glass": "🍷",
    "cocktail": "🍸",
    "tropical_drink": "🍹",
    "beer": "🍺",
    "beer_mug": "🍺",
    "champagne": "🍾",
    "sake": "🍶",
    "coffee": "☕",
    "tea": "🍵",
    "mate": "🧉",
    "pizza": "🍕",
    "sushi": "🍣",
    "ramen": "🍜",
    "noodles": "🍝",
    "spaghetti": "🍝",
    "rice": "🍚",
    "curry": "🍛",
    "taco": "🌮",
    "burrito": "🌯",
    "falafel": "🧆",
    "croissant": "🥐",
    "baguette": "🥖",
    "pretzel": "🥨",
    "cookie": "🍪",
    "cake": "🎂",
    "ice_cream": "🍦",
    "shaved_ice": "🍧",
    "doughnut": "🍩",
    "chocolate": "🍫",
    "candy": "🍬",
    "cheese": "🧀",
    "meat": "🥩",
    "poultry_leg": "🍗",
    "lobster": "🦞",
    "crab": "🦀",
    "shrimp": "🦐",
    "oyster": "🦪",
    "grapes": "🍇",
    "watermelon": "🍉",
    "mango": "🥭",
    "coconut": "🥥",
    "avocado": "🥑",
    "hot_pepper": "🌶️",
    "garlic": "🧄",
    "onion": "🧅",
    "olive": "🫒",
    "flatbread": "🫓",
    "fondue": "🫕",
    "pot_of_food": "🍲",
    "dumpling": "🥟",
    "fortune_cookie": "🥠",
    "takeout_box": "🥡",
    "bento": "🍱",
    "oden": "🍢",
    "dango": "🍡",
    "moon_cake": "🥮",

    # Culture & Arts
    "dancer": "💃",
    "man_dancing": "🕺",
    "performing_arts": "🎭",
    "art": "🎨",
    "palette": "🎨",
    "musical_note": "🎵",
    "notes": "🎶",
    "guitar": "🎸",
    "drum": "🥁",
    "violin": "🎻",
    "saxophone": "🎷",
    "trumpet": "🎺",
    "accordion": "🪗",
    "banjo": "🪕",
    "microphone": "🎤",
    "headphones": "🎧",
    "camera": "📷",
    "camera_flash": "📸",
    "film_frames": "🎞️",
    "movie_camera": "🎥",
    "clapper": "🎬",
    "television": "📺",
    "scroll": "📜",
    "books": "📚",
    "book": "📖",
    "paintbrush": "🖌️",
    "crayon": "🖍️",
    "frame": "🖼️",
    "thread": "🧵",
    "yarn": "🧶",
    "kimono": "👘",
    "sari": "🥻",

    # Activities & Sports
    "diving_mask": "🤿",
    "snorkel": "🤿",
    "surfing": "🏄",
    "surf": "🏄",
    "swimming": "🏊",
    "swim": "🏊",
    "ski": "⛷️",
    "skiing": "⛷️",
    "snowboarder": "🏂",
    "snowboard": "🏂",
    "hiking_boot": "🥾",
    "hiking": "🥾",
    "person_climbing": "🧗",
    "climbing": "🧗",
    "person_biking": "🚴",
    "cycling": "🚴",
    "golf": "⛳",
    "golfing": "🏌️",
    "tennis": "🎾",
    "basketball": "🏀",
    "soccer": "⚽",
    "football": "🏈",
    "volleyball": "🏐",
    "rugby": "🏉",
    "cricket": "🏏",
    "badminton": "🏸",
    "table_tennis": "🏓",
    "hockey": "🏒",
    "ice_skate": "⛸️",
    "curling": "🥌",
    "bow_and_arrow": "🏹",
    "fishing": "🎣",
    "fish_hook": "🎣",
    "running": "🏃",
    "yoga": "🧘",
    "meditation": "🧘",
    "wrestling": "🤼",
    "martial_arts": "🥋",
    "boxing": "🥊",
    "weightlifting": "🏋️",
    "gymnastics": "🤸",
    "cartwheeling": "🤸",
    "parachute": "🪂",
    "parasailing": "🪂",
    "kite": "🪁",
    "playground": "🛝",
    "roller_coaster": "🎢",
    "ferris_wheel": "🎡",
    "carousel": "🎠",

    # Animals
    "elephant": "🐘",
    "lion": "🦁",
    "tiger": "🐅",
    "leopard": "🐆",
    "monkey": "🐒",
    "gorilla": "🦍",
    "orangutan": "🦧",
    "whale": "🐋",
    "whale_spouting": "🐳",
    "dolphin": "🐬",
    "shark": "🦈",
    "seal": "🦭",
    "turtle": "🐢",
    "crocodile": "🐊",
    "snake": "🐍",
    "lizard": "🦎",
    "fish": "🐟",
    "tropical_fish": "🐠",
    "blowfish": "🐡",
    "octopus": "🐙",
    "jellyfish": "🪼",
    "bird": "🐦",
    "eagle": "🦅",
    "parrot": "🦜",
    "flamingo": "🦩",
    "peacock": "🦚",
    "swan": "🦢",
    "owl": "🦉",
    "penguin": "🐧",
    "camel": "🐪",
    "two_hump_camel": "🐫",
    "llama": "🦙",
    "giraffe": "🦒",
    "zebra": "🦓",
    "buffalo": "🦬",
    "bison": "🦬",
    "ox": "🐂",
    "cow": "🐄",
    "horse": "🐎",
    "deer": "🦌",
    "reindeer": "🦌",
    "moose": "🫎",
    "kangaroo": "🦘",
    "koala": "🐨",
    "panda": "🐼",
    "sloth": "🦥",
    "otter": "🦦",
    "beaver": "🦫",
    "polar_bear": "🐻‍❄️",
    "bear": "🐻",
    "raccoon": "🦝",
    "fox": "🦊",
    "wolf": "🐺",
    "bat": "🦇",
    "butterfly": "🦋",
    "bee": "🐝",
    "ladybug": "🐞",
    "cricket_insect": "🦗",
    "scorpion": "🦂",
    "spider": "🕷️",
    "crab": "🦀",
    "lobster": "🦞",

    # Additional missing emojis found in data
    "moyai": "🗿",
    "pyramid": "🗿",
    "sphinx": "🗿",
    "chocolate_bar": "🍫",
    "water": "💧",
    "droplet": "💧",
    "bridge_at_night": "🌉",
    "hotsprings": "♨️",
    "christmas_tree": "🎄",
    "temple": "🛕",
    "spa": "💆",
    "motor_scooter": "🛵",
    "meat_on_bone": "🍖",
    "military_helmet": "🪖",
    "building": "🏢",
    "blossom": "🌸",
    "shopping_cart": "🛒",
    "slot_machine": "🎰",
    "city_sunset": "🌇",
    "small_airplane": "🛩️",
    "surfing_man": "🏄",
    "house_with_garden": "🏡",
    "stew": "🍲",
    "water_buffalo": "🐃",
    "person": "🧑",
    "hotel": "🏨",
    "car": "🚗",
    "island": "🏝️",
    "cityscape": "🏙️",
    "lotus": "🪷",
    "ice_cube": "🧊",

    # Miscellaneous
    "gem": "💎",
    "diamond": "💎",
    "crown": "👑",
    "fire": "🔥",
    "sparkles": "✨",
    "star": "⭐",
    "glowing_star": "🌟",
    "rainbow": "🌈",
    "sun": "☀️",
    "sun_with_face": "🌞",
    "moon": "🌙",
    "crescent_moon": "🌙",
    "full_moon": "🌕",
    "umbrella": "☂️",
    "umbrella_with_rain": "☔",
    "snowflake": "❄️",
    "hot_springs": "♨️",
    "onsen": "♨️",
    "compass": "🧭",
    "world_map": "🗺️",
    "map": "🗺️",
    "globe": "🌍",
    "earth": "🌍",
    "tent": "⛺",
    "camping": "🏕️",
    "house": "🏠",
    "hut": "🛖",
    "shopping_bags": "🛍️",
    "shopping": "🛍️",
    "briefcase": "💼",
    "money_bag": "💰",
    "dollar": "💵",
    "euro": "💶",
    "yen": "💴",
    "credit_card": "💳",
    "passport": "📘",
    "ticket": "🎟️",
    "admission_ticket": "🎫",
    "luggage": "🧳",
    "suitcase": "🧳",
    "key": "🔑",
    "door": "🚪",
    "window": "🪟",
    "bed": "🛏️",
    "couch": "🛋️",
    "bathtub": "🛁",
    "shower": "🚿",
    "toothbrush": "🪥",
    "soap": "🧼",
    "lotion": "🧴",
    "razor": "🪒",
    "mirror": "🪞",
    "candle": "🕯️",
    "lamp": "🪔",
    "flashlight": "🔦",
    "diya_lamp": "🪔",
    "lantern": "🏮",
    "wind_chime": "🎐",
    "red_envelope": "🧧",
    "gift": "🎁",
    "balloon": "🎈",
    "party_popper": "🎉",
    "confetti": "🎊",
    "fireworks": "🎆",
    "sparkler": "🎇",
    "trophy": "🏆",
    "medal": "🏅",
    "first_place": "🥇",
    "second_place": "🥈",
    "third_place": "🥉",
    "flag": "🚩",
    "checkered_flag": "🏁",
    "triangular_flag": "🚩",
}


async def fix_emojis():
    """Fix text emoji names to Unicode in all country_profiles."""
    print(f"Connecting to MongoDB: {MONGODB_URI[:40]}...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB]
    collection = db.country_profiles

    # Get all profiles
    profiles = await collection.find({}).to_list(length=None)
    print(f"Found {len(profiles)} country profiles")

    updated_count = 0
    emoji_fixes = []

    for profile in profiles:
        country_code = profile.get("country_code", "??")
        country_name = profile.get("country_name", "Unknown")
        activities = profile.get("top_activities", [])

        modified = False
        fixes_for_country = []

        for i, activity in enumerate(activities):
            emoji = activity.get("emoji", "")

            # Check if it's a text name (not already Unicode)
            if emoji and emoji in EMOJI_FIX_MAP:
                new_emoji = EMOJI_FIX_MAP[emoji]
                activities[i]["emoji"] = new_emoji
                fixes_for_country.append(f"{emoji} -> {new_emoji}")
                modified = True
            # Also check if it's a short text that looks like a name (no emoji chars)
            elif emoji and len(emoji) > 2 and emoji.isascii() and emoji.replace("_", "").isalpha():
                # It's likely a text name we don't have in our map
                print(f"  WARNING: Unknown emoji name '{emoji}' in {country_code}")

        if modified:
            # Update the document
            result = await collection.update_one(
                {"country_code": country_code},
                {"$set": {
                    "top_activities": activities,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            if result.modified_count > 0:
                updated_count += 1
                print(f"  {country_code} ({country_name}): {', '.join(fixes_for_country)}")
                emoji_fixes.extend(fixes_for_country)

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Profiles updated: {updated_count}")
    print(f"Total emoji fixes: {len(emoji_fixes)}")

    if emoji_fixes:
        print(f"\nUnique fixes applied:")
        unique_fixes = set(emoji_fixes)
        for fix in sorted(unique_fixes):
            print(f"  {fix}")

    client.close()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(fix_emojis())
