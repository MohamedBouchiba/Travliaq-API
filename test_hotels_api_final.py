"""Comprehensive test for Hotels API with corrected parameters."""

import asyncio
import httpx
import json
import sys
from datetime import date, timedelta

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

API_KEY = "xpR8a221kKmshz3a8P4Q0AMYYqAWp17qwO2jsn3JBNWU98tof0"
BASE_URL = "https://booking-com15.p.rapidapi.com/api/v1"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "booking-com15.p.rapidapi.com",
    "Accept": "application/json"
}


async def test_search_destination():
    """Test searchDestination endpoint."""
    print("=" * 60)
    print("TEST 1: searchDestination")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        params = {"query": "Paris", "locale": "en-gb"}
        response = await client.get(
            f"{BASE_URL}/hotels/searchDestination",
            headers=HEADERS,
            params=params
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("status"):
                results = data.get("data", [])
                print(f"Found {len(results)} destinations")
                if results:
                    dest = results[0]
                    print(f"First: {dest.get('name')} (ID: {dest.get('dest_id')}, Type: {dest.get('dest_type')})")
                    return dest.get("dest_id"), dest.get("dest_type")
        return None, None


async def test_search_hotels(dest_id: str, dest_type: str):
    """Test searchHotels with corrected parameters."""
    print("\n" + "=" * 60)
    print("TEST 2: searchHotels (corrected params)")
    print("=" * 60)

    if not dest_id:
        print("SKIP - no dest_id")
        return None

    checkin = date.today() + timedelta(days=30)
    checkout = checkin + timedelta(days=2)

    params = {
        "dest_id": dest_id,
        "search_type": dest_type.upper(),  # CITY, not city
        "arrival_date": str(checkin),
        "departure_date": str(checkout),
        "adults": "2",
        "room_qty": "1",
        "page_number": "1",
        "currency_code": "EUR",
        "languagecode": "en-gb",
        "sort_by": "popularity"
    }

    print(f"Params: {json.dumps(params, indent=2)}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(
            f"{BASE_URL}/hotels/searchHotels",
            headers=HEADERS,
            params=params
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Top keys: {list(data.keys())}")

            if data.get("status"):
                inner = data.get("data", {})
                print(f"Data keys: {list(inner.keys())}")
                hotels = inner.get("hotels", [])
                print(f"Hotels count: {len(hotels)}")

                if hotels:
                    h = hotels[0]
                    hotel_id = h.get("hotel_id")
                    prop = h.get("property", {})

                    print(f"\nFirst hotel (new structure):")
                    print(f"  hotel_id: {hotel_id}")
                    print(f"  name: {prop.get('name', 'N/A')}")
                    print(f"  reviewScore: {prop.get('reviewScore', 'N/A')}")
                    print(f"  reviewCount: {prop.get('reviewCount', 'N/A')}")
                    print(f"  propertyClass: {prop.get('propertyClass', 'N/A')} stars")

                    # Price extraction
                    price_breakdown = prop.get("priceBreakdown", {})
                    if price_breakdown:
                        gross = price_breakdown.get("grossPrice", {})
                        print(f"  grossPrice: {gross.get('value', 'N/A')} {gross.get('currency', 'EUR')}")

                    return hotel_id
            else:
                print(f"API status=false: {data.get('message')}")
    return None


async def test_get_hotel_details(hotel_id: str):
    """Test getHotelDetails."""
    print("\n" + "=" * 60)
    print("TEST 3: getHotelDetails")
    print("=" * 60)

    if not hotel_id:
        print("SKIP - no hotel_id")
        return

    checkin = date.today() + timedelta(days=30)
    checkout = checkin + timedelta(days=2)

    params = {
        "hotel_id": str(hotel_id),
        "arrival_date": str(checkin),
        "departure_date": str(checkout),
        "adults": "2",
        "currency_code": "EUR",
        "languagecode": "en-gb"
    }

    print(f"Params: {params}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(
            f"{BASE_URL}/hotels/getHotelDetails",
            headers=HEADERS,
            params=params
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Top keys: {list(data.keys())}")

            if data.get("status"):
                inner = data.get("data", {})
                print(f"Data keys (first 15): {list(inner.keys())[:15]}")
                print(f"Hotel name: {inner.get('hotel_name', inner.get('name', 'N/A'))}")
                print(f"Address: {inner.get('address', 'N/A')}")
                print(f"Review score: {inner.get('review_score', 'N/A')}")
                print(f"Class: {inner.get('class', 'N/A')} stars")
            else:
                print(f"API status=false: {data.get('message')}")


async def test_get_hotel_rooms(hotel_id: str):
    """Test getRooms."""
    print("\n" + "=" * 60)
    print("TEST 4: getRooms")
    print("=" * 60)

    if not hotel_id:
        print("SKIP - no hotel_id")
        return

    checkin = date.today() + timedelta(days=30)
    checkout = checkin + timedelta(days=2)

    params = {
        "hotel_id": str(hotel_id),
        "arrival_date": str(checkin),
        "departure_date": str(checkout),
        "adults": "2",
        "room_qty": "1",
        "currency_code": "EUR",
        "languagecode": "en-gb"
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(
            f"{BASE_URL}/hotels/getRooms",
            headers=HEADERS,
            params=params
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("status"):
                inner = data.get("data", {})
                print(f"Data keys: {list(inner.keys())[:10]}")

                # Try to find rooms
                rooms = inner.get("rooms", inner.get("block", []))
                if isinstance(rooms, dict):
                    rooms = list(rooms.values())

                print(f"Rooms found: {len(rooms) if rooms else 0}")
                if rooms and len(rooms) > 0:
                    r = rooms[0]
                    print(f"First room: {r.get('room_name', r.get('name', 'N/A'))}")
            else:
                print(f"API status=false: {data.get('message')}")


async def test_get_hotel_photos(hotel_id: str):
    """Test getHotelPhotos."""
    print("\n" + "=" * 60)
    print("TEST 5: getHotelPhotos")
    print("=" * 60)

    if not hotel_id:
        print("SKIP - no hotel_id")
        return

    params = {
        "hotel_id": str(hotel_id),
        "locale": "en-gb"
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(
            f"{BASE_URL}/hotels/getHotelPhotos",
            headers=HEADERS,
            params=params
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("status"):
                photos = data.get("data", [])
                print(f"Photos count: {len(photos)}")
                if photos:
                    p = photos[0]
                    url = p.get("url_max", p.get("url_original", p.get("url", "N/A")))
                    print(f"First photo URL: {url[:80]}..." if len(url) > 80 else f"First photo URL: {url}")
            else:
                print(f"API status=false: {data.get('message')}")


async def main():
    print("=" * 60)
    print("COMPREHENSIVE HOTELS API TEST")
    print("=" * 60)
    print()

    # Test 1: Search destination
    dest_id, dest_type = await test_search_destination()

    # Test 2: Search hotels
    hotel_id = await test_search_hotels(dest_id, dest_type)

    # Test 3: Hotel details
    await test_get_hotel_details(hotel_id)

    # Test 4: Rooms
    await test_get_hotel_rooms(hotel_id)

    # Test 5: Photos
    await test_get_hotel_photos(hotel_id)

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)

    if hotel_id:
        print(f"\nSUCCESS: API working correctly with corrected parameters")
        print(f"Test hotel ID: {hotel_id}")
    else:
        print(f"\nWARNING: Could not retrieve hotel data")


if __name__ == "__main__":
    asyncio.run(main())
