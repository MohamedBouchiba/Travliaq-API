"""Debug script for Booking.com Hotels API."""

import asyncio
import httpx
import json
from datetime import date, timedelta

API_KEY = "xpR8a221kKmshz3a8P4Q0AMYYqAWp17qwO2jsn3JBNWU98tof0"
BASE_URL = "https://booking-com15.p.rapidapi.com/api/v1"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "booking-com15.p.rapidapi.com",
    "Accept": "application/json"
}


async def debug_search_hotels():
    """Debug searchHotels with raw output."""
    print("="*60)
    print("DEBUG: searchHotels raw response")
    print("="*60)

    checkin = date.today() + timedelta(days=14)
    checkout = checkin + timedelta(days=3)

    params = {
        "dest_id": "-1456928",  # Paris
        "dest_type": "city",
        "checkin_date": str(checkin),
        "checkout_date": str(checkout),
        "adults_number": "2",
        "room_number": "1",
        "filter_by_currency": "EUR",
        "locale": "en-gb",
        "order_by": "popularity",
        "page_number": "0",
        "units": "metric"
    }

    print(f"\nRequest params:")
    print(json.dumps(params, indent=2))

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/hotels/searchHotels",
            headers=HEADERS,
            params=params
        )

        print(f"\nStatus: {response.status_code}")
        print(f"\nRaw response (first 2000 chars):")
        print(response.text[:2000])

        if response.status_code == 200:
            data = response.json()
            print(f"\n\nJSON keys at root level: {list(data.keys()) if isinstance(data, dict) else 'list'}")

            if isinstance(data, dict):
                if "data" in data:
                    print(f"JSON keys in 'data': {list(data['data'].keys()) if isinstance(data['data'], dict) else 'list/other'}")
                if "result" in data:
                    print(f"'result' type: {type(data['result'])}")
                if "hotels" in data:
                    print(f"'hotels' count: {len(data['hotels'])}")


async def debug_search_with_arrival_date():
    """Try with different date parameter names."""
    print("\n" + "="*60)
    print("DEBUG: Try arrival_date instead of checkin_date")
    print("="*60)

    checkin = date.today() + timedelta(days=14)
    checkout = checkin + timedelta(days=3)

    # Try different param names
    params = {
        "dest_id": "-1456928",
        "dest_type": "city",
        "arrival_date": str(checkin),  # Try this instead
        "departure_date": str(checkout),  # Try this instead
        "adults": "2",
        "room_qty": "1",
        "currency_code": "EUR",
        "languagecode": "en-gb"
    }

    print(f"\nRequest params:")
    print(json.dumps(params, indent=2))

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/hotels/searchHotels",
            headers=HEADERS,
            params=params
        )

        print(f"\nStatus: {response.status_code}")
        print(f"\nRaw response (first 1500 chars):")
        print(response.text[:1500])


async def debug_search_simple():
    """Try minimal params."""
    print("\n" + "="*60)
    print("DEBUG: Minimal params search")
    print("="*60)

    checkin = date.today() + timedelta(days=30)
    checkout = checkin + timedelta(days=2)

    # Minimal required params
    params = {
        "dest_id": "-1456928",
        "search_type": "city",  # Try search_type
        "arrival_date": str(checkin),
        "departure_date": str(checkout),
        "adults": "2"
    }

    print(f"Params: {params}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/hotels/searchHotels",
            headers=HEADERS,
            params=params
        )

        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        print(f"First 1000 chars: {response.text[:1000]}")


async def try_different_endpoints():
    """Try different hotel search endpoints."""
    print("\n" + "="*60)
    print("DEBUG: Try different endpoints")
    print("="*60)

    checkin = date.today() + timedelta(days=30)
    checkout = checkin + timedelta(days=2)

    endpoints = [
        "/hotels/searchHotels",
        "/hotels/search",
        "/hotels/getHotels",
        "/properties/list",
    ]

    params = {
        "dest_id": "-1456928",
        "dest_type": "city",
        "checkin_date": str(checkin),
        "checkout_date": str(checkout),
        "adults_number": "2",
        "room_number": "1"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint in endpoints:
            print(f"\nTrying: {endpoint}")
            try:
                response = await client.get(
                    f"{BASE_URL}{endpoint}",
                    headers=HEADERS,
                    params=params
                )
                print(f"  Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"  Keys: {list(data.keys())[:5]}")
                        if "data" in data:
                            inner = data["data"]
                            if isinstance(inner, dict):
                                print(f"  data keys: {list(inner.keys())[:5]}")
                            elif isinstance(inner, list):
                                print(f"  data is list, len={len(inner)}")
            except Exception as e:
                print(f"  Error: {e}")


async def main():
    await debug_search_hotels()
    await debug_search_with_arrival_date()
    await debug_search_simple()
    await try_different_endpoints()


if __name__ == "__main__":
    asyncio.run(main())
