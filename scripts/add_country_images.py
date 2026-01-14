#!/usr/bin/env python3
"""
Script to generate AI images for country profiles using OpenRouter/Flux 2 Pro
and upload them to Supabase Storage.

Based on the image-comparison-tool service.

Usage:
    python scripts/add_country_images.py

Environment variables (from .env):
    MONGODB_URI: MongoDB connection string for Travliaq API
    MONGODB_DB: Database name (travliaq)

Required: OpenRouter API key and Supabase credentials (hardcoded from image-comparison-tool)
"""

import asyncio
import base64
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient

# ============================================================================
# CONFIGURATION - Using same config as image-comparison-tool
# ============================================================================

OPENROUTER_API_KEY = "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"
SUPABASE_URL = "https://cinbnmlfpffmyjmkwbco.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNpbmJubWxmcGZmbXlqbWt3YmNvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Nzk0NDYxNCwiZXhwIjoyMDczNTIwNjE0fQ.rhAShncXPpDQwkunA9hETknNk0kr9IaLATTY5404Ht0"
SUPABASE_BUCKET = "Country"

# Storage mode: "supabase" (recommended) or "local"
STORAGE_MODE = "supabase"
LOCAL_IMAGES_DIR = Path(__file__).parent / "generated_images"

BATCH_SIZE = 10
PAUSE_BETWEEN_REQUESTS = 3  # seconds
PROGRESS_FILE = Path(__file__).parent / "country_images_progress.json"


# ============================================================================
# COUNTRY PROMPTS - Tailored prompts for each country
# Format: country_code -> (prompt, description_fr)
# ============================================================================

COUNTRY_PROMPTS = {
    # === EUROPE ===
    "FR": (
        "Eiffel Tower Paris at golden hour, romantic atmosphere, cherry blossoms, travel photography, cinematic",
        "Tour Eiffel, Paris"
    ),
    "ES": (
        "Sagrada Familia Barcelona aerial view, Gaudi architecture, golden sunset, travel photography, stunning",
        "Sagrada Familia, Barcelone"
    ),
    "IT": (
        "Venice Grand Canal gondolas, colorful buildings, sunset reflection, romantic Italy, travel photography",
        "Grand Canal, Venise"
    ),
    "PT": (
        "Lisbon colorful tram street, historic Alfama district, yellow tram, Portuguese tiles, travel photography",
        "Tramway de Lisbonne"
    ),
    "GR": (
        "Santorini white houses blue domes, Aegean sea view, Greek islands, sunset, travel photography stunning",
        "Santorini, Grece"
    ),
    "HR": (
        "Dubrovnik old town walls, Adriatic sea, Game of Thrones location, Croatian coast, travel photography",
        "Dubrovnik, Croatie"
    ),
    "NL": (
        "Amsterdam canal houses, bicycles, tulips, traditional Dutch architecture, spring, travel photography",
        "Canaux d'Amsterdam"
    ),
    "DE": (
        "Neuschwanstein castle Bavaria, fairytale castle, Alps mountains, autumn colors, travel photography",
        "Chateau de Neuschwanstein"
    ),
    "GB": (
        "London Big Ben Tower Bridge, Thames river, red double decker bus, iconic British landmarks, travel",
        "Big Ben, Londres"
    ),
    "AT": (
        "Vienna Schonbrunn Palace gardens, baroque architecture, Austrian elegance, travel photography stunning",
        "Palais de Schonbrunn, Vienne"
    ),
    "CH": (
        "Swiss Alps Matterhorn, snow peaks, alpine lake reflection, Switzerland landscape, travel photography",
        "Cervin, Alpes Suisses"
    ),
    "BE": (
        "Brussels Grand Place, golden baroque buildings, Belgian chocolate, night illumination, travel photo",
        "Grand Place, Bruxelles"
    ),
    "CZ": (
        "Prague Charles Bridge at dawn, Gothic towers, Vltava river, Czech Republic, travel photography stunning",
        "Pont Charles, Prague"
    ),
    "HU": (
        "Budapest Parliament building, Danube river, chain bridge, Hungarian architecture, night, travel photo",
        "Parlement de Budapest"
    ),
    "PL": (
        "Krakow Main Square, St Mary Basilica, Polish medieval city, colorful buildings, travel photography",
        "Place du marche, Cracovie"
    ),
    "IE": (
        "Cliffs of Moher Ireland, dramatic Atlantic coast, green hills, Irish landscape, travel photography",
        "Falaises de Moher, Irlande"
    ),
    "DK": (
        "Copenhagen Nyhavn colorful harbor, Danish design, boats, Scandinavian charm, travel photography",
        "Nyhavn, Copenhague"
    ),
    "SE": (
        "Stockholm old town Gamla Stan, Swedish architecture, Baltic sea, Nordic city, travel photography",
        "Gamla Stan, Stockholm"
    ),
    "NO": (
        "Norwegian fjords, dramatic cliffs, emerald water, Norway landscape, northern lights, travel photography",
        "Fjords de Norvege"
    ),
    "FI": (
        "Finnish Lapland northern lights, aurora borealis, snow forest, Finland winter, travel photography",
        "Aurores boreales, Laponie"
    ),
    "IS": (
        "Iceland blue lagoon geothermal spa, volcanic landscape, steam, Icelandic nature, travel photography",
        "Blue Lagoon, Islande"
    ),
    "RO": (
        "Bran Castle Transylvania, Dracula castle, Romanian mountains, Gothic architecture, travel photography",
        "Chateau de Bran, Roumanie"
    ),

    # === ASIA ===
    "TH": (
        "Thailand floating market Bangkok, Buddhist temples, tropical paradise, Thai culture, travel photography",
        "Temple bouddhiste, Thailande"
    ),
    "JP": (
        "Mount Fuji cherry blossoms Japan, pagoda, spring sakura, Japanese landscape, travel photography stunning",
        "Mont Fuji, Japon"
    ),
    "VN": (
        "Ha Long Bay Vietnam, limestone karsts, emerald water, traditional boats, Vietnamese landscape, travel",
        "Baie d'Ha Long, Vietnam"
    ),
    "ID": (
        "Bali rice terraces Tegallalang, lush green, Indonesian temple, tropical paradise, travel photography",
        "Rizieres de Bali"
    ),
    "MY": (
        "Kuala Lumpur Petronas Towers, Malaysian modern city, twin towers night, travel photography stunning",
        "Tours Petronas, Kuala Lumpur"
    ),
    "SG": (
        "Singapore Marina Bay Sands, Gardens by the Bay, futuristic city, night lights, travel photography",
        "Marina Bay, Singapour"
    ),
    "PH": (
        "Philippines Palawan island, crystal clear water, limestone cliffs, tropical beach, travel photography",
        "Palawan, Philippines"
    ),
    "KR": (
        "Seoul Gyeongbokgung Palace, Korean traditional architecture, cherry blossoms, travel photography",
        "Palais Gyeongbokgung, Seoul"
    ),
    "CN": (
        "Great Wall of China, ancient wonder, mountains, Chinese landmark, dramatic landscape, travel photography",
        "Grande Muraille de Chine"
    ),
    "HK": (
        "Hong Kong skyline Victoria Peak, neon lights, harbor view, Asian metropolis, night, travel photography",
        "Skyline de Hong Kong"
    ),
    "IN": (
        "Taj Mahal Agra India, marble mausoleum, sunrise, Indian architecture, wonder of world, travel photography",
        "Taj Mahal, Inde"
    ),
    "LK": (
        "Sri Lanka Sigiriya rock fortress, ancient palace, tropical jungle, Lankan landscape, travel photography",
        "Sigiriya, Sri Lanka"
    ),
    "NP": (
        "Nepal Himalayas Mount Everest, prayer flags, Buddhist monastery, mountain landscape, travel photography",
        "Himalaya, Nepal"
    ),
    "MV": (
        "Maldives overwater bungalows, turquoise lagoon, tropical paradise, luxury resort, travel photography",
        "Bungalows sur pilotis, Maldives"
    ),

    # === MIDDLE EAST ===
    "AE": (
        "Dubai Burj Khalifa skyline, futuristic city, desert oasis, UAE architecture, night, travel photography",
        "Burj Khalifa, Dubai"
    ),
    "TR": (
        "Istanbul Hagia Sophia Blue Mosque, Turkish architecture, Bosphorus, Ottoman heritage, travel photography",
        "Sainte-Sophie, Istanbul"
    ),
    "IL": (
        "Jerusalem old city Western Wall, golden dome, holy land, Israeli heritage, travel photography stunning",
        "Vieille ville de Jerusalem"
    ),
    "JO": (
        "Petra Treasury Jordan, ancient carved city, rose red rocks, Nabataean architecture, travel photography",
        "Petra, Jordanie"
    ),
    "OM": (
        "Oman Muscat Grand Mosque, Arabian architecture, desert landscape, Middle East, travel photography",
        "Grande Mosquee, Mascate"
    ),
    "QA": (
        "Qatar Doha skyline, modern architecture, Persian Gulf, futuristic city, night, travel photography",
        "Skyline de Doha, Qatar"
    ),

    # === AMERICAS ===
    "US": (
        "New York City skyline Statue of Liberty, Manhattan, American landmark, sunset, travel photography",
        "Statue de la Liberte, New York"
    ),
    "CA": (
        "Canadian Rockies Banff, turquoise lake Louise, mountains reflection, Canada landscape, travel photography",
        "Lac Louise, Canada"
    ),
    "MX": (
        "Mexico Chichen Itza pyramid, Mayan ruins, ancient civilization, Mexican heritage, travel photography",
        "Chichen Itza, Mexique"
    ),
    "BR": (
        "Rio de Janeiro Christ the Redeemer, Sugarloaf mountain, Brazilian coast, sunset, travel photography",
        "Christ Redempteur, Rio"
    ),
    "AR": (
        "Argentina Perito Moreno glacier, Patagonia ice, turquoise water, dramatic landscape, travel photography",
        "Glacier Perito Moreno"
    ),
    "PE": (
        "Machu Picchu Peru, Inca citadel, Andes mountains, ancient ruins, mystical, travel photography stunning",
        "Machu Picchu, Perou"
    ),
    "CL": (
        "Chile Torres del Paine, Patagonia mountains, dramatic peaks, South American landscape, travel photography",
        "Torres del Paine, Chili"
    ),
    "CO": (
        "Colombia Cartagena colorful streets, colonial architecture, Caribbean coast, Latin America, travel photo",
        "Cartagena, Colombie"
    ),
    "CR": (
        "Costa Rica rainforest waterfall, tropical wildlife, lush jungle, Pura Vida, travel photography stunning",
        "Foret tropicale, Costa Rica"
    ),
    "PA": (
        "Panama Canal ships, engineering marvel, tropical landscape, Central America, travel photography",
        "Canal de Panama"
    ),
    "CU": (
        "Havana Cuba vintage cars, colorful colonial buildings, Caribbean charm, Cuban culture, travel photography",
        "Voitures vintage, La Havane"
    ),
    "DO": (
        "Dominican Republic Punta Cana beach, palm trees, turquoise Caribbean sea, tropical paradise, travel",
        "Plage de Punta Cana"
    ),
    "JM": (
        "Jamaica tropical beach, reggae culture, palm trees, Caribbean island, turquoise water, travel photography",
        "Plage de Jamaique"
    ),

    # === AFRICA ===
    "MA": (
        "Morocco Marrakech medina, colorful souks, Moroccan tiles, Atlas mountains, travel photography stunning",
        "Medina de Marrakech"
    ),
    "EG": (
        "Egypt Pyramids of Giza Sphinx, ancient wonder, desert sunset, Egyptian landmark, travel photography",
        "Pyramides de Gizeh"
    ),
    "ZA": (
        "South Africa Cape Town Table Mountain, dramatic coast, African landscape, sunset, travel photography",
        "Montagne de la Table"
    ),
    "KE": (
        "Kenya Masai Mara safari, African wildlife, elephants savanna, sunset, travel photography stunning",
        "Safari Masai Mara, Kenya"
    ),
    "TZ": (
        "Tanzania Serengeti wildebeest migration, African safari, golden savanna, wildlife, travel photography",
        "Serengeti, Tanzanie"
    ),
    "TN": (
        "Tunisia Sidi Bou Said, blue white village, Mediterranean coast, North Africa, travel photography",
        "Sidi Bou Said, Tunisie"
    ),
    "MU": (
        "Mauritius tropical beach, turquoise lagoon, palm trees, Indian Ocean paradise, travel photography",
        "Plage de l'Ile Maurice"
    ),
    "SC": (
        "Seychelles Anse Source d'Argent, granite boulders, pristine beach, tropical paradise, travel photography",
        "Anse Source d'Argent"
    ),
    "SN": (
        "Senegal Dakar, African culture, colorful markets, West Africa, vibrant city, travel photography",
        "Dakar, Senegal"
    ),
    "CV": (
        "Cape Verde volcanic islands, Atlantic ocean, African paradise, dramatic landscape, travel photography",
        "Iles du Cap-Vert"
    ),

    # === OCEANIA ===
    "AU": (
        "Australia Sydney Opera House harbour bridge, Australian landmark, sunset, travel photography stunning",
        "Opera de Sydney"
    ),
    "NZ": (
        "New Zealand Milford Sound, dramatic fjords, mountains reflection, Kiwi landscape, travel photography",
        "Milford Sound, Nouvelle-Zelande"
    ),
    "FJ": (
        "Fiji tropical islands, crystal clear water, palm trees, South Pacific paradise, travel photography",
        "Iles Fidji"
    ),
    "PF": (
        "Tahiti French Polynesia, overwater bungalows, turquoise lagoon, Bora Bora, travel photography stunning",
        "Bora Bora, Polynesie"
    ),

    # === ISLANDS & OTHERS ===
    "CY": (
        "Cyprus Mediterranean coast, ancient ruins, turquoise sea, Greek island charm, travel photography",
        "Cote de Chypre"
    ),
    "MT": (
        "Malta Valletta harbor, golden limestone, Mediterranean architecture, historic fortress, travel photography",
        "La Valette, Malte"
    ),
}


def generate_prompt(country_name: str, landmark_prompt: str) -> str:
    """Generate the full prompt for AI image generation."""
    return f"""A real photograph of {landmark_prompt}, the most famous landmark of {country_name}, taken by a tourist with a good camera.

The photo shows a single iconic place that represents {country_name} - the kind of photo you would find on Google Images or TripAdvisor.

Photo characteristics:
- Looks like a real photo taken on location, not a composite or artistic rendering
- Natural daylight, realistic shadows
- Single viewpoint, single location
- The kind of image a travel blogger would post
- High resolution, sharp focus on the main subject

NO composites, NO multiple landmarks merged together, NO artistic interpretations, NO illustrations, NO CGI, NO text, NO watermarks.

Just a simple, beautiful, realistic travel photo of {country_name}."""


def generate_image_openrouter(country_name: str, landmark_prompt: str) -> str:
    """Generate an image via OpenRouter/Flux 2 Pro. Returns base64 data."""
    prompt = generate_prompt(country_name, landmark_prompt)

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "black-forest-labs/flux.2-pro",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "modalities": ["image", "text"]
        },
        timeout=120
    )

    result = response.json()

    if result.get("choices"):
        message = result["choices"][0]["message"]
        if message.get("images"):
            image_data = message["images"][0]["image_url"]["url"]
            # Extract base64 from "data:image/png;base64,..."
            if image_data.startswith("data:"):
                base64_data = image_data.split(",")[1]
                return base64_data

    # Check for errors
    if result.get("error"):
        raise Exception(f"OpenRouter error: {result['error']}")

    raise Exception(f"No image generated: {result}")


def sanitize_filename(name: str) -> str:
    """Clean a name for use in a filename."""
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')


def save_image_locally(base64_data: str, country_code: str, country_name: str) -> str:
    """Save an image locally. Returns the file path."""
    LOCAL_IMAGES_DIR.mkdir(exist_ok=True)

    image_bytes = base64.b64decode(base64_data)
    safe_name = sanitize_filename(country_name)
    filename = f"{country_code}_{safe_name}_ai_generated.png"
    filepath = LOCAL_IMAGES_DIR / filename

    with open(filepath, 'wb') as f:
        f.write(image_bytes)

    return str(filepath.absolute())


def upload_to_supabase(base64_data: str, country_code: str) -> str:
    """Upload an image to Supabase Storage. Returns the public URL."""
    image_bytes = base64.b64decode(base64_data)
    filename = f"{country_code}_ai_generated.png"

    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"

    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "image/png",
        "x-upsert": "true"  # Replace if exists
    }

    response = requests.post(url, headers=headers, data=image_bytes, timeout=60)

    if response.status_code in [200, 201]:
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"
        return public_url
    else:
        raise Exception(f"Supabase upload error: {response.status_code} - {response.text}")


def load_progress() -> dict:
    """Load progress from file."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"completed": [], "failed": [], "skipped": []}


def save_progress(progress: dict):
    """Save progress to file."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


async def update_country_images():
    """Main function to generate and upload images for all countries."""
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Connect to Travliaq API MongoDB (using Atlas)
    uri = os.getenv(
        "MONGODB_URI",
        "mongodb+srv://teamtravliaq_db_user:DUfRgh8TkEDJHSlT@travliaq-countrybasis.wljfuyy.mongodb.net/?retryWrites=true&w=majority&appName=Travliaq-CountryBasis"
    )
    db_name = os.getenv("MONGODB_DB", "travliaq_knowledge_base")

    print(f"Connecting to MongoDB: {uri[:40]}...")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    collection = db.country_profiles

    # Load progress
    progress = load_progress()
    completed = set(progress["completed"])

    # Filter countries that need images
    countries_to_process = [
        (code, prompt_data) for code, prompt_data in COUNTRY_PROMPTS.items()
        if code not in completed
    ]

    total = len(countries_to_process)
    print(f"\n{'='*60}")
    print(f"AI Image Generation for Country Profiles")
    print(f"{'='*60}")
    print(f"Service: OpenRouter / Flux 1.1 Pro")
    print(f"Storage: {STORAGE_MODE.upper()}")
    print(f"Total to generate: {total}")
    print(f"Already completed: {len(completed)}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"{'='*60}\n")

    if total == 0:
        print("All images already generated!")
        client.close()
        return

    processed = 0
    errors = 0

    for i, (code, (prompt, description)) in enumerate(countries_to_process):
        # Get country name from database
        profile = await collection.find_one({"country_code": code})
        if not profile:
            print(f"[{i+1}/{total}] {code}: Profile not found in DB - SKIPPING")
            progress["skipped"].append(code)
            save_progress(progress)
            continue

        country_name = profile.get("country_name", code)

        print(f"[{i+1}/{total}] {country_name} ({code})")
        print(f"         Landmark: {description}")

        try:
            # Generate image
            print(f"         -> Generating via Flux 1.1 Pro...")
            base64_data = generate_image_openrouter(country_name, prompt)

            # Save/upload image
            if STORAGE_MODE == "supabase":
                print(f"         -> Uploading to Supabase...")
                image_url = upload_to_supabase(base64_data, code)
            else:
                print(f"         -> Saving locally...")
                image_url = save_image_locally(base64_data, code, country_name)

            # Update MongoDB
            print(f"         -> Updating MongoDB...")
            await collection.update_one(
                {"country_code": code},
                {"$set": {
                    "photo_url": image_url,
                    "photo_credit": "Generated by AI (Flux 1.1 Pro)",
                    "photo_source": "OpenRouter/Flux",
                    "photo_landmark": description,
                    "updated_at": datetime.utcnow()
                }}
            )

            # Mark as completed
            progress["completed"].append(code)
            save_progress(progress)

            print(f"         -> OK: {image_url[:60]}...")
            processed += 1

        except Exception as e:
            print(f"         -> ERROR: {e}")
            progress["failed"].append({
                "code": code,
                "name": country_name,
                "error": str(e)
            })
            save_progress(progress)
            errors += 1

        # Pause between requests
        if i + 1 < total:
            print(f"         -> Waiting {PAUSE_BETWEEN_REQUESTS}s...")
            time.sleep(PAUSE_BETWEEN_REQUESTS)

        # Pause after each batch
        if (i + 1) % BATCH_SIZE == 0 and i + 1 < total:
            print(f"\n{'='*60}")
            print(f"Batch completed ({BATCH_SIZE} images)")
            print(f"Progress: {i+1}/{total}")
            print(f"Pausing 10s before next batch...")
            print(f"(Press Ctrl+C to stop and resume later)")
            print(f"{'='*60}\n")
            time.sleep(10)

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Successfully generated: {processed}")
    print(f"Errors: {errors}")
    print(f"Skipped: {len(progress['skipped'])}")

    if progress['failed']:
        print(f"\nFailed countries:")
        for item in progress['failed'][-5:]:  # Show last 5 errors
            print(f"  - {item['name']} ({item['code']}): {item['error'][:50]}...")

    client.close()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(update_country_images())
