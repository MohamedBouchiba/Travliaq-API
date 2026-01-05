"""Test with correct API parameters."""

import asyncio
import httpx
import json
from datetime import date, timedelta
import sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

API_KEY = "xpR8a221kKmshz3a8P4Q0AMYYqAWp17qwO2jsn3JBNWU98tof0"
BASE_URL = "https://booking-com15.p.rapidapi.com/api/v1"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "booking-com15.p.rapidapi.com",
    "Accept": "application/json"
}


async def test_correct_search():
    """Test with corrected parameters."""
    print("="*60)
    print("TEST: searchHotels with correct params")
    print("="*60)

    checkin = date.today() + timedelta(days=30)
    checkout = checkin + timedelta(days=2)

    # Correct parameters based on error messages
    params = {
        "dest_id": "-1456928",  # Paris
        "search_type": "CITY",  # Instead of dest_type
        "arrival_date": str(checkin),  # Instead of checkin_date
        "departure_date": str(checkout),  # Instead of checkout_date
        "adults": "2",
        "room_qty": "1",
        "page_number": "1",  # Try 1 instead of 0
        "currency_code": "EUR",
        "languagecode": "en-gb"
    }

    print(f"\nParams: {json.dumps(params, indent=2)}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(
            f"{BASE_URL}/hotels/searchHotels",
            headers=HEADERS,
            params=params
        )

        print(f"\nStatus: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Keys: {list(data.keys())}")

            if data.get("status") == True:
                print("SUCCESS! API returned valid data")
                inner = data.get("data", {})
                if isinstance(inner, dict):
                    print(f"Data keys: {list(inner.keys())}")
                    hotels = inner.get("hotels", [])
                    print(f"Hotels count: {len(hotels)}")

                    if hotels:
                        h = hotels[0]
                        print(f"\nFirst hotel:")
                        print(f"  hotel_id: {h.get('hotel_id')}")
                        print(f"  name: {h.get('property', {}).get('name', h.get('hotel_name', 'N/A'))}")
                        print(f"  review_score: {h.get('property', {}).get('reviewScore', 'N/A')}")

                        # Try to find price
                        price_info = h.get('property', {}).get('priceBreakdown', {})
                        if price_info:
                            gross = price_info.get('grossPrice', {})
                            print(f"  price: {gross.get('value', 'N/A')} {gross.get('currency', 'EUR')}")

                        return h.get('hotel_id')
            else:
                print(f"API returned status=false")
                print(f"Message: {data.get('message')}")
                # Try to see what data is there anyway
                if "data" in data:
                    inner = data["data"]
                    if isinstance(inner, dict):
                        print(f"Data keys anyway: {list(inner.keys())}")
                        if "hotels" in inner:
                            print(f"Hotels count: {len(inner['hotels'])}")
        else:
            print(f"HTTP Error: {response.status_code}")

    return None


async def test_get_details(hotel_id: str):
    """Test hotel details with correct params."""
    print("\n" + "="*60)
    print("TEST: getHotelDetails")
    print("="*60)

    if not hotel_id:
        print("Skipping - no hotel ID")
        return

    checkin = date.today() + timedelta(days=30)
    checkout = checkin + timedelta(days=2)

    params = {
        "hotel_id": hotel_id,
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
            print(f"Keys: {list(data.keys())}")

            if data.get("status") == True:
                inner = data.get("data", {})
                print(f"Data keys: {list(inner.keys())[:10]}")
                print(f"Hotel name: {inner.get('hotel_name', inner.get('name', 'N/A'))}")
                print(f"Address: {inner.get('address', 'N/A')}")


async def main():
    hotel_id = await test_correct_search()
    await test_get_details(hotel_id)
    print("\n" + "="*60)
    print("TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
