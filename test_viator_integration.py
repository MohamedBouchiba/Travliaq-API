"""
Test script for Viator API integration.

This script performs basic smoke tests to verify the Viator integration is working correctly.
Run this after starting the API server.

Usage:
    python test_viator_integration.py
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any


BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/v1/activities/search"


def print_result(test_name: str, success: bool, details: str = ""):
    """Print test result with formatting."""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"    {details}")
    print()


async def test_search_by_city():
    """Test searching activities by city name."""
    print("=" * 60)
    print("TEST 1: Search by City Name (Paris)")
    print("=" * 60)

    start_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    request_data = {
        "location": {
            "city": "Paris",
            "country_code": "FR"
        },
        "dates": {
            "start_date": start_date
        },
        "pagination": {
            "page": 1,
            "page_size": 5
        },
        "currency": "EUR",
        "language": "en"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(API_ENDPOINT, json=request_data)

            if response.status_code == 200:
                data = response.json()

                if data.get("success"):
                    total = data.get("results", {}).get("total", 0)
                    activities = data.get("results", {}).get("activities", [])
                    cached = data.get("cache_info", {}).get("cached", False)

                    details = f"Found {total} activities, returned {len(activities)}"
                    details += f", cached: {cached}"

                    if activities:
                        first = activities[0]
                        details += f"\n    First result: {first.get('title', 'N/A')}"
                        details += f"\n    Price: {first.get('pricing', {}).get('from_price', 'N/A')} {first.get('pricing', {}).get('currency', '')}"
                        details += f"\n    Rating: {first.get('rating', {}).get('average', 'N/A')}/5"

                    print_result("Search by city", True, details)
                    return True
                else:
                    error = data.get("error", {})
                    print_result("Search by city", False, f"API error: {error}")
                    return False
            else:
                print_result("Search by city", False, f"HTTP {response.status_code}: {response.text}")
                return False

    except Exception as e:
        print_result("Search by city", False, f"Exception: {str(e)}")
        return False


async def test_search_with_filters():
    """Test searching with category and rating filters."""
    print("=" * 60)
    print("TEST 2: Search with Filters (Museum, Rating >= 4.0)")
    print("=" * 60)

    start_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    request_data = {
        "location": {
            "city": "Rome",
            "country_code": "IT"
        },
        "dates": {
            "start_date": start_date
        },
        "filters": {
            "categories": ["museum"],
            "min_rating": 4.0
        },
        "pagination": {
            "page": 1,
            "page_size": 5
        },
        "currency": "EUR",
        "language": "en"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(API_ENDPOINT, json=request_data)

            if response.status_code == 200:
                data = response.json()

                if data.get("success"):
                    activities = data.get("results", {}).get("activities", [])

                    # Verify all results meet filter criteria
                    all_match = True
                    for activity in activities:
                        rating = activity.get("rating", {}).get("average", 0)
                        if rating < 4.0:
                            all_match = False
                            break

                    details = f"Found {len(activities)} activities"
                    if all_match and activities:
                        details += ", all match rating filter"

                    print_result("Search with filters", all_match, details)
                    return all_match
                else:
                    print_result("Search with filters", False, f"API error: {data.get('error')}")
                    return False
            else:
                print_result("Search with filters", False, f"HTTP {response.status_code}")
                return False

    except Exception as e:
        print_result("Search with filters", False, f"Exception: {str(e)}")
        return False


async def test_cache_functionality():
    """Test that cache is working by making the same request twice."""
    print("=" * 60)
    print("TEST 3: Cache Functionality")
    print("=" * 60)

    start_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    request_data = {
        "location": {
            "city": "Barcelona",
            "country_code": "ES"
        },
        "dates": {
            "start_date": start_date
        },
        "pagination": {
            "page": 1,
            "page_size": 3
        },
        "currency": "EUR",
        "language": "en"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First request (should not be cached)
            print("Making first request (cache miss expected)...")
            response1 = await client.post(API_ENDPOINT, json=request_data)

            if response1.status_code != 200:
                print_result("Cache test", False, f"First request failed: HTTP {response1.status_code}")
                return False

            data1 = response1.json()
            cached1 = data1.get("cache_info", {}).get("cached", False)

            # Second request (should be cached)
            print("Making second request (cache hit expected)...")
            await asyncio.sleep(1)  # Small delay
            response2 = await client.post(API_ENDPOINT, json=request_data)

            if response2.status_code != 200:
                print_result("Cache test", False, f"Second request failed: HTTP {response2.status_code}")
                return False

            data2 = response2.json()
            cached2 = data2.get("cache_info", {}).get("cached", False)

            # Verify cache behavior
            success = not cached1 and cached2
            details = f"First request cached: {cached1}, Second request cached: {cached2}"

            if success:
                details += "\n    Cache working correctly!"
            else:
                details += "\n    Cache not working as expected"

            print_result("Cache functionality", success, details)
            return success

    except Exception as e:
        print_result("Cache test", False, f"Exception: {str(e)}")
        return False


async def test_invalid_location():
    """Test error handling for invalid location."""
    print("=" * 60)
    print("TEST 4: Invalid Location Handling")
    print("=" * 60)

    start_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    request_data = {
        "location": {
            "city": "InvalidCityThatDoesNotExist123456",
            "country_code": "XX"
        },
        "dates": {
            "start_date": start_date
        },
        "currency": "EUR",
        "language": "en"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(API_ENDPOINT, json=request_data)

            # Should return 400 or error response
            if response.status_code == 400:
                data = response.json()
                error_code = data.get("detail", {}).get("error", {}).get("code", "")

                success = error_code == "INVALID_LOCATION"
                details = f"Returned expected error code: {error_code}"
                print_result("Invalid location handling", success, details)
                return success
            else:
                # Also accept 200 with success: false
                if response.status_code == 200:
                    data = response.json()
                    if not data.get("success"):
                        print_result("Invalid location handling", True, "Returned success: false")
                        return True

                print_result("Invalid location handling", False, f"Unexpected response: HTTP {response.status_code}")
                return False

    except Exception as e:
        print_result("Invalid location handling", False, f"Exception: {str(e)}")
        return False


async def test_image_variants():
    """Test that image variants are properly returned."""
    print("=" * 60)
    print("TEST 5: Image Variants")
    print("=" * 60)

    start_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    request_data = {
        "location": {
            "city": "London",
            "country_code": "GB"
        },
        "dates": {
            "start_date": start_date
        },
        "pagination": {
            "page": 1,
            "page_size": 3
        },
        "currency": "GBP",
        "language": "en"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(API_ENDPOINT, json=request_data)

            if response.status_code == 200:
                data = response.json()

                if data.get("success"):
                    activities = data.get("results", {}).get("activities", [])

                    if not activities:
                        print_result("Image variants", False, "No activities returned")
                        return False

                    # Check first activity has images with variants
                    first = activities[0]
                    images = first.get("images", [])

                    if not images:
                        print_result("Image variants", False, "No images in first activity")
                        return False

                    first_image = images[0]
                    variants = first_image.get("variants", {})

                    has_variants = bool(variants)
                    details = f"Found {len(images)} images"
                    if has_variants:
                        variant_sizes = list(variants.keys())
                        details += f"\n    Variants available: {', '.join(variant_sizes)}"

                    print_result("Image variants", has_variants, details)
                    return has_variants
                else:
                    print_result("Image variants", False, "API returned success: false")
                    return False
            else:
                print_result("Image variants", False, f"HTTP {response.status_code}")
                return False

    except Exception as e:
        print_result("Image variants", False, f"Exception: {str(e)}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("VIATOR API INTEGRATION TEST SUITE")
    print("=" * 60)
    print(f"Testing endpoint: {API_ENDPOINT}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n")

    # Check if server is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/docs")
            if response.status_code != 200:
                print("ERROR: API server not responding at", BASE_URL)
                print("Please start the server with: uvicorn app.main:app --reload")
                return
    except Exception as e:
        print(f"ERROR: Cannot connect to API server at {BASE_URL}")
        print(f"Error: {str(e)}")
        print("\nPlease start the server with: uvicorn app.main:app --reload")
        return

    # Run tests
    results = []

    results.append(await test_search_by_city())
    await asyncio.sleep(1)

    results.append(await test_search_with_filters())
    await asyncio.sleep(1)

    results.append(await test_cache_functionality())
    await asyncio.sleep(1)

    results.append(await test_invalid_location())
    await asyncio.sleep(1)

    results.append(await test_image_variants())

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total*100):.1f}%")

    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print(f"\n✗ {total - passed} test(s) failed")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
