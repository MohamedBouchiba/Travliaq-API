"""
Test script to inspect actual Viator API response structure for location data.
This will help us understand where coordinates actually come from.
"""
import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

VIATOR_API_KEY = os.getenv("VIATOR_API_KEY_DEV") or os.getenv("VIATOR_API_KEY_PROD")
VIATOR_BASE_URL = "https://api.viator.com"

async def test_viator_structure():
    """Test Viator API to understand actual data structure."""

    if not VIATOR_API_KEY:
        print("ERROR: No Viator API key found in environment")
        return

    print(f"Using Viator API key: {VIATOR_API_KEY[:10]}...")
    print(f"Base URL: {VIATOR_BASE_URL}")
    print("=" * 80)

    headers = {
        "Accept": "application/json;version=2.0",
        "Accept-Language": "en-US",
        "exp-api-key": VIATOR_API_KEY
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Search for products in Paris
        print("\n1. Searching for products in Paris (destination 479)...")
        search_payload = {
            "filtering": {
                "destination": "479",
                "startDate": "2026-06-01",
                "endDate": "2026-06-07"
            },
            "pagination": {
                "start": 1,
                "count": 3  # Just get 3 products for testing
            },
            "currency": "EUR"
        }

        response = await client.post(
            f"{VIATOR_BASE_URL}/partner/products/search",
            headers=headers,
            json=search_payload
        )

        if response.status_code != 200:
            print(f"ERROR: Search failed with status {response.status_code}")
            print(response.text)
            return

        search_data = response.json()
        products = search_data.get("products", [])

        print(f"Found {len(products)} products")
        print("\nProduct codes:")
        for p in products:
            print(f"  - {p.get('productCode')}: {p.get('title')}")

        if not products:
            print("No products found!")
            return

        # Step 2: Get full details for first product
        product_code = products[0].get("productCode")
        print(f"\n{'=' * 80}")
        print(f"2. Fetching FULL details for product: {product_code}")
        print(f"{'=' * 80}")

        response = await client.get(
            f"{VIATOR_BASE_URL}/partner/products/{product_code}",
            headers=headers
        )

        if response.status_code != 200:
            print(f"ERROR: Product details failed with status {response.status_code}")
            print(response.text)
            return

        product = response.json()

        # Save full response for inspection
        with open("viator_product_full.json", "w", encoding="utf-8") as f:
            json.dump(product, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Full product data saved to: viator_product_full.json")

        # Analyze logistics structure
        print(f"\n{'=' * 80}")
        print("3. LOGISTICS STRUCTURE:")
        print(f"{'=' * 80}")
        logistics = product.get("logistics", {})
        print(f"Logistics keys: {list(logistics.keys())}")

        # Check for start/end points
        if "start" in logistics:
            start_points = logistics["start"]
            print(f"\n  ✓ logistics.start exists: {len(start_points)} points")
            if start_points:
                print(f"\n  First start point structure:")
                print(json.dumps(start_points[0], indent=4))
        else:
            print("\n  ✗ logistics.start does NOT exist")

        if "end" in logistics:
            end_points = logistics["end"]
            print(f"\n  ✓ logistics.end exists: {len(end_points)} points")
            if end_points:
                print(f"\n  First end point structure:")
                print(json.dumps(end_points[0], indent=4))
        else:
            print("\n  ✗ logistics.end does NOT exist")

        # Check travelerPickup
        if "travelerPickup" in logistics:
            pickup = logistics["travelerPickup"]
            print(f"\n  logistics.travelerPickup:")
            print(json.dumps(pickup, indent=4))

        # Analyze itinerary structure
        print(f"\n{'=' * 80}")
        print("4. ITINERARY STRUCTURE:")
        print(f"{'=' * 80}")
        itinerary = product.get("itinerary", {})
        print(f"Itinerary keys: {list(itinerary.keys())}")

        if "days" in itinerary:
            days = itinerary["days"]
            print(f"\n  ✓ itinerary.days exists: {len(days)} days")
            if days:
                print(f"\n  First day structure:")
                day = days[0]
                print(f"    Day keys: {list(day.keys())}")

                items = day.get("items", [])
                print(f"    Items: {len(items)}")
                if items:
                    print(f"\n    First item structure:")
                    item = items[0]
                    print(json.dumps(item, indent=6))
        else:
            print("\n  ✗ itinerary.days does NOT exist")

        # Check other potential location sources
        print(f"\n{'=' * 80}")
        print("5. OTHER POTENTIAL LOCATION SOURCES:")
        print(f"{'=' * 80}")

        # Check destinations
        destinations = product.get("destinations", [])
        print(f"\nDestinations: {len(destinations)}")
        if destinations:
            print(json.dumps(destinations[0], indent=2))

        # Summary
        print(f"\n{'=' * 80}")
        print("6. SUMMARY - WHERE TO FIND COORDINATES:")
        print(f"{'=' * 80}")

        found_coords = []

        # Check logistics.start
        if "start" in logistics:
            for idx, point in enumerate(logistics.get("start", [])):
                loc = point.get("location", {})
                if loc.get("ref") or loc.get("latitude") or loc.get("lat"):
                    found_coords.append(f"logistics.start[{idx}]")

        # Check logistics.end
        if "end" in logistics:
            for idx, point in enumerate(logistics.get("end", [])):
                loc = point.get("location", {})
                if loc.get("ref") or loc.get("latitude") or loc.get("lat"):
                    found_coords.append(f"logistics.end[{idx}]")

        # Check itinerary
        if "days" in itinerary:
            for day_idx, day in enumerate(itinerary.get("days", [])):
                for item_idx, item in enumerate(day.get("items", [])):
                    poi = item.get("pointOfInterest", {})
                    loc = poi.get("location", {})
                    if loc.get("ref") or loc.get("latitude") or loc.get("lat"):
                        found_coords.append(f"itinerary.days[{day_idx}].items[{item_idx}].pointOfInterest")

        if found_coords:
            print("\n✅ Location data found in:")
            for path in found_coords:
                print(f"  - {path}")
        else:
            print("\n❌ NO location data found in logistics or itinerary!")
            print("\n⚠️  This product may not have detailed location information.")
            print("    Coordinates might only be available via destination-level data.")

        # Test with 2nd and 3rd products
        print(f"\n{'=' * 80}")
        print("7. TESTING OTHER PRODUCTS:")
        print(f"{'=' * 80}")

        for i in range(1, min(3, len(products))):
            product_code = products[i].get("productCode")
            print(f"\nProduct {i+1}: {product_code}")

            response = await client.get(
                f"{VIATOR_BASE_URL}/partner/products/{product_code}",
                headers=headers
            )

            if response.status_code == 200:
                prod = response.json()
                has_logistics_start = bool(prod.get("logistics", {}).get("start"))
                has_logistics_end = bool(prod.get("logistics", {}).get("end"))
                has_itinerary_days = bool(prod.get("itinerary", {}).get("days"))

                print(f"  - logistics.start: {'✓' if has_logistics_start else '✗'}")
                print(f"  - logistics.end: {'✓' if has_logistics_end else '✗'}")
                print(f"  - itinerary.days: {'✓' if has_itinerary_days else '✗'}")
            else:
                print(f"  ERROR: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(test_viator_structure())
