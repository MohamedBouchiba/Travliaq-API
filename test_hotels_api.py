"""Test script for Booking.com Hotels API integration."""

import asyncio
import httpx
import json
from datetime import date, timedelta

# API Configuration
API_KEY = "xpR8a221kKmshz3a8P4Q0AMYYqAWp17qwO2jsn3JBNWU98tof0"
BASE_URL = "https://booking-com15.p.rapidapi.com/api/v1"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "booking-com15.p.rapidapi.com",
    "Accept": "application/json"
}


async def test_search_destination():
    """Test 1: Search for destinations."""
    print("\n" + "="*60)
    print("TEST 1: searchDestination")
    print("="*60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        for city in ["Paris", "Lyon", "Barcelona"]:
            print(f"\nSearching for: {city}")

            response = await client.get(
                f"{BASE_URL}/hotels/searchDestination",
                headers=HEADERS,
                params={"query": city}
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # Handle different response formats
                if isinstance(data, dict) and "data" in data:
                    results = data["data"]
                elif isinstance(data, list):
                    results = data
                else:
                    results = []

                print(f"Results found: {len(results)}")

                if results:
                    first = results[0]
                    print(f"  First result:")
                    print(f"    - dest_id: {first.get('dest_id')}")
                    print(f"    - dest_type: {first.get('dest_type')}")
                    print(f"    - name: {first.get('name', first.get('city_name', 'N/A'))}")
                    print(f"    - country: {first.get('country', 'N/A')}")

                    return first.get('dest_id'), first.get('dest_type')
            else:
                print(f"Error: {response.text[:200]}")

    return None, None


async def test_search_hotels(dest_id: str, dest_type: str):
    """Test 2: Search for hotels."""
    print("\n" + "="*60)
    print("TEST 2: searchHotels")
    print("="*60)

    if not dest_id:
        print("Skipping - no destination ID")
        return None

    # Dates: 2 weeks from now for 3 nights
    checkin = date.today() + timedelta(days=14)
    checkout = checkin + timedelta(days=3)

    params = {
        "dest_id": dest_id,
        "dest_type": dest_type,
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

    print(f"\nSearching hotels in {dest_id} ({dest_type})")
    print(f"Dates: {checkin} to {checkout}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/hotels/searchHotels",
            headers=HEADERS,
            params=params
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # Handle response format
            if isinstance(data, dict):
                if "data" in data:
                    data = data["data"]

                hotels = data.get("hotels", data.get("result", []))
                total = data.get("count", data.get("total_count", len(hotels)))

                print(f"Total hotels: {total}")
                print(f"Hotels in response: {len(hotels)}")

                if hotels:
                    hotel = hotels[0]
                    hotel_id = hotel.get("hotel_id", hotel.get("id"))

                    print(f"\nFirst hotel:")
                    print(f"  - hotel_id: {hotel_id}")
                    print(f"  - name: {hotel.get('hotel_name', hotel.get('name', 'N/A'))}")
                    print(f"  - address: {hotel.get('address', 'N/A')}")
                    print(f"  - review_score: {hotel.get('review_score', 'N/A')}")
                    print(f"  - class (stars): {hotel.get('class', 'N/A')}")

                    # Extract price
                    price_data = hotel.get("price_breakdown", hotel.get("composite_price_breakdown", {}))
                    if isinstance(price_data, dict):
                        gross = price_data.get("gross_amount_per_night", price_data.get("gross_amount", {}))
                        if isinstance(gross, dict):
                            print(f"  - price/night: {gross.get('value', 'N/A')} {gross.get('currency', 'EUR')}")
                    elif "min_total_price" in hotel:
                        print(f"  - min_total_price: {hotel.get('min_total_price', 'N/A')}")

                    # Check coordinates
                    lat = hotel.get("latitude", hotel.get("lat"))
                    lng = hotel.get("longitude", hotel.get("lng", hotel.get("lon")))
                    print(f"  - coordinates: {lat}, {lng}")

                    return str(hotel_id)
        else:
            print(f"Error: {response.text[:500]}")

    return None


async def test_hotel_details(hotel_id: str):
    """Test 3: Get hotel details."""
    print("\n" + "="*60)
    print("TEST 3: getHotelDetails")
    print("="*60)

    if not hotel_id:
        print("Skipping - no hotel ID")
        return

    checkin = date.today() + timedelta(days=14)
    checkout = checkin + timedelta(days=3)

    params = {
        "hotel_id": hotel_id,
        "checkin_date": str(checkin),
        "checkout_date": str(checkout),
        "adults_number": "2",
        "locale": "en-gb",
        "currency_code": "EUR"
    }

    print(f"\nGetting details for hotel: {hotel_id}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/hotels/getHotelDetails",
            headers=HEADERS,
            params=params
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if isinstance(data, dict) and "data" in data:
                data = data["data"]

            print(f"\nHotel details:")
            print(f"  - name: {data.get('hotel_name', data.get('name', 'N/A'))}")
            print(f"  - address: {data.get('address', 'N/A')}")
            print(f"  - review_score: {data.get('review_score', 'N/A')}")
            print(f"  - review_nr: {data.get('review_nr', 'N/A')}")
            print(f"  - class: {data.get('class', 'N/A')}")
            print(f"  - checkin: {data.get('checkin', 'N/A')}")
            print(f"  - checkout: {data.get('checkout', 'N/A')}")

            # Description
            desc = data.get('description', data.get('hotel_description', ''))
            if desc:
                print(f"  - description: {desc[:100]}...")

            return True
        else:
            print(f"Error: {response.text[:500]}")

    return False


async def test_hotel_photos(hotel_id: str):
    """Test 4: Get hotel photos."""
    print("\n" + "="*60)
    print("TEST 4: getHotelPhotos")
    print("="*60)

    if not hotel_id:
        print("Skipping - no hotel ID")
        return

    params = {
        "hotel_id": hotel_id,
        "locale": "en-gb"
    }

    print(f"\nGetting photos for hotel: {hotel_id}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/hotels/getHotelPhotos",
            headers=HEADERS,
            params=params
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if isinstance(data, dict) and "data" in data:
                photos = data["data"]
            elif isinstance(data, list):
                photos = data
            else:
                photos = []

            print(f"Photos found: {len(photos)}")

            if photos:
                first = photos[0]
                print(f"\nFirst photo:")
                print(f"  - url_max: {first.get('url_max', first.get('url_original', 'N/A'))[:80]}...")
        else:
            print(f"Error: {response.text[:300]}")


async def test_hotel_rooms(hotel_id: str):
    """Test 5: Get hotel rooms."""
    print("\n" + "="*60)
    print("TEST 5: getRooms")
    print("="*60)

    if not hotel_id:
        print("Skipping - no hotel ID")
        return

    checkin = date.today() + timedelta(days=14)
    checkout = checkin + timedelta(days=3)

    params = {
        "hotel_id": hotel_id,
        "checkin_date": str(checkin),
        "checkout_date": str(checkout),
        "adults_number": "2",
        "room_number": "1",
        "currency_code": "EUR",
        "locale": "en-gb"
    }

    print(f"\nGetting rooms for hotel: {hotel_id}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/hotels/getRooms",
            headers=HEADERS,
            params=params
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if isinstance(data, dict) and "data" in data:
                data = data["data"]

            rooms = data.get("rooms", data.get("block", []))
            if isinstance(rooms, dict):
                rooms = list(rooms.values())

            print(f"Rooms found: {len(rooms)}")

            if rooms:
                room = rooms[0]
                print(f"\nFirst room:")
                print(f"  - name: {room.get('room_name', room.get('name', 'N/A'))}")
                print(f"  - max_occupancy: {room.get('max_occupancy', 'N/A')}")
                print(f"  - is_free_cancellable: {room.get('is_free_cancellable', 'N/A')}")
        else:
            print(f"Error: {response.text[:300]}")


async def test_map_prices_simulation():
    """Test 6: Simulate map-prices (multiple city searches)."""
    print("\n" + "="*60)
    print("TEST 6: map-prices simulation (3 cities)")
    print("="*60)

    cities = ["Paris", "Lyon", "Marseille"]
    checkin = date.today() + timedelta(days=14)
    checkout = checkin + timedelta(days=3)

    results = {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        for city in cities:
            print(f"\nFetching price for: {city}")

            # Step 1: Get destination
            dest_response = await client.get(
                f"{BASE_URL}/hotels/searchDestination",
                headers=HEADERS,
                params={"query": city}
            )

            if dest_response.status_code != 200:
                print(f"  Error getting destination")
                continue

            dest_data = dest_response.json()
            if isinstance(dest_data, dict) and "data" in dest_data:
                dest_data = dest_data["data"]

            if not dest_data:
                print(f"  No destination found")
                continue

            dest = dest_data[0]
            dest_id = dest.get("dest_id")
            dest_type = dest.get("dest_type", "city")

            # Step 2: Search hotels (sorted by price, limit 1)
            hotels_response = await client.get(
                f"{BASE_URL}/hotels/searchHotels",
                headers=HEADERS,
                params={
                    "dest_id": dest_id,
                    "dest_type": dest_type,
                    "checkin_date": str(checkin),
                    "checkout_date": str(checkout),
                    "adults_number": "2",
                    "room_number": "1",
                    "filter_by_currency": "EUR",
                    "order_by": "price",
                    "page_number": "0"
                }
            )

            if hotels_response.status_code != 200:
                print(f"  Error getting hotels")
                continue

            hotels_data = hotels_response.json()
            if isinstance(hotels_data, dict) and "data" in hotels_data:
                hotels_data = hotels_data["data"]

            hotels = hotels_data.get("hotels", hotels_data.get("result", []))

            if hotels:
                hotel = hotels[0]
                price_data = hotel.get("price_breakdown", hotel.get("composite_price_breakdown", {}))
                min_price = None

                if isinstance(price_data, dict):
                    gross = price_data.get("gross_amount_per_night", price_data.get("gross_amount", {}))
                    if isinstance(gross, dict):
                        min_price = gross.get("value")
                    elif isinstance(gross, (int, float)):
                        min_price = gross

                if min_price is None and "min_total_price" in hotel:
                    min_price = float(hotel["min_total_price"]) / 3  # 3 nights

                results[city] = min_price
                print(f"  Min price: {min_price} EUR")
            else:
                print(f"  No hotels found")

    print(f"\n\nMap prices results:")
    print(json.dumps(results, indent=2))


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("BOOKING.COM API TESTS")
    print("="*60)

    # Test 1: Search destination
    dest_id, dest_type = await test_search_destination()

    # Test 2: Search hotels
    hotel_id = await test_search_hotels(dest_id, dest_type)

    # Test 3: Hotel details
    await test_hotel_details(hotel_id)

    # Test 4: Hotel photos
    await test_hotel_photos(hotel_id)

    # Test 5: Hotel rooms
    await test_hotel_rooms(hotel_id)

    # Test 6: Map prices simulation
    await test_map_prices_simulation()

    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
