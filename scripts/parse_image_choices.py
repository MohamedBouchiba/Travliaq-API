#!/usr/bin/env python3
"""
Parse image_choices.json and extract chosen URLs for each country.
Also list countries with "none" choice that need images generated.
"""

import json
import sys
from pathlib import Path

# Read the image_choices.json file
choices_file = Path("/home/mohamed-bouchiba/Bureau/Travliaq/image_choices.json")

with open(choices_file, "r", encoding="utf-8") as f:
    choices = json.load(f)

# Separate countries by choice type
countries_with_url = {}
countries_with_none = []

for code, data in choices.items():
    country_name = data.get("country_name", code)
    choice = data.get("choice", "none")

    if choice == "none":
        countries_with_none.append({"code": code, "name": country_name})
    elif choice == "image_1":
        url = data.get("photo_url_1")
        if url:
            countries_with_url[code] = {"name": country_name, "url": url}
    elif choice == "image_2":
        url = data.get("photo_url_2")
        if url:
            countries_with_url[code] = {"name": country_name, "url": url}

# Print results
print("=" * 60)
print(f"TOTAL COUNTRIES: {len(choices)}")
print(f"Countries with chosen URL: {len(countries_with_url)}")
print(f"Countries with 'none' (need images): {len(countries_with_none)}")
print("=" * 60)

print("\n--- COUNTRIES WITH CHOSEN URLS ---")
for code, info in sorted(countries_with_url.items()):
    print(f"{code}: {info['name']}")
    print(f"   URL: {info['url'][:80]}...")

print("\n" + "=" * 60)
print("--- COUNTRIES WITH 'NONE' (NEED IMAGES) ---")
print("=" * 60)
for c in sorted(countries_with_none, key=lambda x: x["code"]):
    print(f"  {c['code']}: {c['name']}")

# Export to JSON for easy use
output = {
    "countries_with_url": countries_with_url,
    "countries_with_none": countries_with_none
}

output_file = Path("/home/mohamed-bouchiba/Bureau/Travliaq/Travliaq-API/scripts/parsed_image_choices.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nExported to: {output_file}")
