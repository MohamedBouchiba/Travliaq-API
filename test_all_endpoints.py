"""Test all hotel endpoints with simple and complex queries."""

import httpx
import asyncio
import json

BASE_URL = "https://travliaq-api-production.up.railway.app"


async def test_search_simple(client):
    """Simple search - just city and dates."""
    print("\n" + "=" * 70)
    print("1. SEARCH - Simple (city + dates)")
    print("=" * 70)

    payload = {
        "city": "Paris",
        "countryCode": "FR",
        "checkIn": "2026-02-15",
        "checkOut": "2026-02-17",
        "rooms": [{"adults": 2}],
        "currency": "EUR",
        "limit": 5
    }

    print(f"Request: POST /api/v1/hotels/search")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    response = await client.post(f"{BASE_URL}/api/v1/hotels/search", json=payload)
    print(f"\nStatus: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        hotels = data.get("results", {}).get("hotels", [])
        print(f"Hotels: {len(hotels)} | Total: {data.get('results', {}).get('total', 0)}")
        for h in hotels[:3]:
            print(f"  - {h.get('name')[:45]:<45} | {h.get('pricePerNight')} EUR | Stars: {h.get('stars') or 'N/A'}")
    return response.status_code == 200


async def test_search_with_filters(client):
    """Complex search with filters and sorting."""
    print("\n" + "=" * 70)
    print("2. SEARCH - Complex (filters + sort + children)")
    print("=" * 70)

    payload = {
        "city": "Barcelona",
        "countryCode": "ES",
        "checkIn": "2026-03-10",
        "checkOut": "2026-03-14",
        "rooms": [
            {"adults": 2, "childrenAges": [5, 8]}
        ],
        "currency": "EUR",
        "limit": 10,
        "filters": {
            "priceMin": 80,
            "priceMax": 250,
            "minStars": 3,
            "minRating": 7.0
        },
        "sort": "price_asc"
    }

    print(f"Request: POST /api/v1/hotels/search")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    response = await client.post(f"{BASE_URL}/api/v1/hotels/search", json=payload)
    print(f"\nStatus: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        hotels = data.get("results", {}).get("hotels", [])
        print(f"Hotels: {len(hotels)} | Total: {data.get('results', {}).get('total', 0)}")
        print(f"Filters applied: {data.get('filters_applied', {})}")
        for h in hotels[:5]:
            print(f"  - {h.get('name')[:40]:<40} | {h.get('pricePerNight')} EUR | Stars: {h.get('stars')} | Rating: {h.get('rating')}")
    return response.status_code == 200


async def test_search_multi_rooms(client):
    """Search with multiple rooms."""
    print("\n" + "=" * 70)
    print("3. SEARCH - Multiple rooms")
    print("=" * 70)

    payload = {
        "city": "Rome",
        "countryCode": "IT",
        "checkIn": "2026-04-01",
        "checkOut": "2026-04-05",
        "rooms": [
            {"adults": 2},
            {"adults": 2, "childrenAges": [3]},
            {"adults": 1}
        ],
        "currency": "EUR",
        "limit": 5
    }

    print(f"Request: POST /api/v1/hotels/search")
    print(f"Rooms: 3 rooms (2+2+1 adults, 1 child)")

    response = await client.post(f"{BASE_URL}/api/v1/hotels/search", json=payload)
    print(f"\nStatus: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        hotels = data.get("results", {}).get("hotels", [])
        print(f"Hotels: {len(hotels)} | Total: {data.get('results', {}).get('total', 0)}")
        for h in hotels[:3]:
            print(f"  - {h.get('name')[:45]:<45} | {h.get('pricePerNight')} EUR/night | Total: {h.get('totalPrice')} EUR")
    return response.status_code == 200


async def test_search_amenities(client):
    """Search with amenity filters."""
    print("\n" + "=" * 70)
    print("4. SEARCH - With amenity filters (wifi + pool)")
    print("=" * 70)

    payload = {
        "city": "Nice",
        "countryCode": "FR",
        "checkIn": "2026-06-15",
        "checkOut": "2026-06-18",
        "rooms": [{"adults": 2}],
        "currency": "EUR",
        "limit": 5,
        "filters": {
            "amenities": ["wifi", "pool"],
            "minStars": 4
        }
    }

    print(f"Request: POST /api/v1/hotels/search")
    print(f"Filters: wifi + pool, 4+ stars")

    response = await client.post(f"{BASE_URL}/api/v1/hotels/search", json=payload)
    print(f"\nStatus: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        hotels = data.get("results", {}).get("hotels", [])
        print(f"Hotels: {len(hotels)} | Total: {data.get('results', {}).get('total', 0)}")
        for h in hotels[:3]:
            print(f"  - {h.get('name')[:40]:<40} | {h.get('pricePerNight')} EUR | Amenities: {h.get('amenities', [])[:5]}")
    return response.status_code == 200


async def test_hotel_details_simple(client, hotel_id):
    """Simple hotel details request."""
    print("\n" + "=" * 70)
    print("5. DETAILS - Simple")
    print("=" * 70)

    params = {
        "checkIn": "2026-02-15",
        "checkOut": "2026-02-17",
        "rooms": "2-0",
        "currency": "EUR"
    }

    print(f"Request: GET /api/v1/hotels/{hotel_id}")
    print(f"Params: {params}")

    response = await client.get(f"{BASE_URL}/api/v1/hotels/{hotel_id}", params=params)
    print(f"\nStatus: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        hotel = data.get("hotel", {})
        print(f"Name: {hotel.get('name')}")
        print(f"Stars: {hotel.get('stars')} | Rating: {hotel.get('rating')}")
        print(f"Address: {hotel.get('address')}")
        print(f"Images: {len(hotel.get('images', []))}")
        print(f"Amenities: {len(hotel.get('amenities', []))}")
        rooms = hotel.get("rooms", [])
        print(f"Rooms available: {len(rooms)}")
        for r in rooms[:2]:
            print(f"  - {r.get('name')[:40]:<40} | {r.get('pricePerNight')} EUR/night")
    return response.status_code == 200


async def test_hotel_details_complex(client, hotel_id):
    """Complex hotel details with multiple rooms and children."""
    print("\n" + "=" * 70)
    print("6. DETAILS - Complex (2 rooms, children)")
    print("=" * 70)

    params = {
        "checkIn": "2026-03-20",
        "checkOut": "2026-03-25",
        "rooms": "2-5-8,2-0",  # Room 1: 2 adults + kids 5,8 | Room 2: 2 adults
        "currency": "EUR",
        "locale": "fr"
    }

    print(f"Request: GET /api/v1/hotels/{hotel_id}")
    print(f"Params: {params}")
    print(f"Rooms format: 2 adults + children(5,8) | 2 adults")

    response = await client.get(f"{BASE_URL}/api/v1/hotels/{hotel_id}", params=params)
    print(f"\nStatus: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        hotel = data.get("hotel", {})
        print(f"Name: {hotel.get('name')}")
        print(f"Cached: {data.get('cache_info', {}).get('cached', False)}")
        rooms = hotel.get("rooms", [])
        print(f"Rooms: {len(rooms)}")
        for r in rooms[:3]:
            print(f"  - {r.get('name')[:35]:<35} | {r.get('pricePerNight')} EUR | Max: {r.get('maxOccupancy')} pers | Free cancel: {r.get('cancellationFree')}")
    return response.status_code == 200


async def test_map_prices_simple(client):
    """Simple map prices for a few cities."""
    print("\n" + "=" * 70)
    print("7. MAP-PRICES - Simple (3 cities)")
    print("=" * 70)

    payload = {
        "cities": [
            {"city": "Paris", "countryCode": "FR"},
            {"city": "Lyon", "countryCode": "FR"},
            {"city": "Marseille", "countryCode": "FR"}
        ],
        "checkIn": "2026-02-15",
        "checkOut": "2026-02-17",
        "rooms": [{"adults": 2}],
        "currency": "EUR"
    }

    print(f"Request: POST /api/v1/hotels/map-prices")
    print(f"Cities: Paris, Lyon, Marseille")

    response = await client.post(f"{BASE_URL}/api/v1/hotels/map-prices", json=payload)
    print(f"\nStatus: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        prices = data.get("prices", {})
        print(f"Prices received for {len(prices)} cities:")
        for city_key, price_data in prices.items():
            if price_data:
                print(f"  - {city_key}: {price_data.get('minPrice')} {price_data.get('currency')}")
            else:
                print(f"  - {city_key}: No data")
    return response.status_code == 200


async def test_map_prices_complex(client):
    """Complex map prices with more cities."""
    print("\n" + "=" * 70)
    print("8. MAP-PRICES - Complex (5 cities, different countries)")
    print("=" * 70)

    payload = {
        "cities": [
            {"city": "Paris", "countryCode": "FR"},
            {"city": "Barcelona", "countryCode": "ES"},
            {"city": "Rome", "countryCode": "IT"},
            {"city": "Amsterdam", "countryCode": "NL"},
            {"city": "Berlin", "countryCode": "DE"}
        ],
        "checkIn": "2026-04-10",
        "checkOut": "2026-04-13",
        "rooms": [{"adults": 2, "childrenAges": [6]}],
        "currency": "EUR"
    }

    print(f"Request: POST /api/v1/hotels/map-prices")
    print(f"Cities: Paris, Barcelona, Rome, Amsterdam, Berlin")
    print(f"With 1 child (age 6)")

    response = await client.post(f"{BASE_URL}/api/v1/hotels/map-prices", json=payload)
    print(f"\nStatus: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        prices = data.get("prices", {})
        print(f"Prices received:")
        for city_key, price_data in sorted(prices.items()):
            if price_data:
                print(f"  - {city_key:<20} | From {price_data.get('minPrice')} {price_data.get('currency')}")
            else:
                print(f"  - {city_key:<20} | No data")
        print(f"Cached: {data.get('cache_info', {}).get('cached', False)}")
    return response.status_code == 200


async def main():
    print("=" * 70)
    print("HOTEL API - COMPLETE TEST SUITE")
    print("=" * 70)
    print(f"Base URL: {BASE_URL}")

    results = {}
    hotel_id_for_details = None

    async with httpx.AsyncClient(timeout=120.0) as client:
        # First clear cache
        print("\nClearing hotel cache...")
        await client.post(f"{BASE_URL}/admin/cache/clear-hotels")

        # Test 1: Simple search
        results["search_simple"] = await test_search_simple(client)

        # Get a hotel ID for details tests
        response = await client.post(
            f"{BASE_URL}/api/v1/hotels/search",
            json={
                "city": "Paris",
                "countryCode": "FR",
                "checkIn": "2026-02-15",
                "checkOut": "2026-02-17",
                "rooms": [{"adults": 2}],
                "currency": "EUR",
                "limit": 1
            }
        )
        if response.status_code == 200:
            hotels = response.json().get("results", {}).get("hotels", [])
            if hotels:
                hotel_id_for_details = hotels[0].get("id")
                print(f"\nUsing hotel ID for details: {hotel_id_for_details}")

        # Test 2: Complex search with filters
        results["search_filters"] = await test_search_with_filters(client)

        # Test 3: Multi-room search
        results["search_multi_rooms"] = await test_search_multi_rooms(client)

        # Test 4: Amenity filters
        results["search_amenities"] = await test_search_amenities(client)

        # Test 5 & 6: Hotel details
        if hotel_id_for_details:
            results["details_simple"] = await test_hotel_details_simple(client, hotel_id_for_details)
            results["details_complex"] = await test_hotel_details_complex(client, hotel_id_for_details)
        else:
            print("\nSkipping details tests - no hotel ID available")
            results["details_simple"] = False
            results["details_complex"] = False

        # Test 7: Simple map prices
        results["map_prices_simple"] = await test_map_prices_simple(client)

        # Test 8: Complex map prices
        results["map_prices_complex"] = await test_map_prices_complex(client)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, passed_test in results.items():
        status = "[PASS]" if passed_test else "[FAIL]"
        print(f"  {test_name:<25} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
