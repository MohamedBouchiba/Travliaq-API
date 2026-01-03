
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock
from app.services.activities_service import ActivitiesService
from app.utils.viator_mapper import ViatorMapper

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_enrichment():
    print("Setting up test...")
    
    # Mock dependencies
    viator_client = AsyncMock()
    viator_products = AsyncMock()
    redis_cache = MagicMock()
    repo = MagicMock()
    tags_repo = MagicMock()
    location_resolver = MagicMock()
    
    service = ActivitiesService(
        viator_client=viator_client,
        viator_products=viator_products,
        redis_cache=redis_cache,
        activities_repo=repo,
        tags_repo=tags_repo,
        location_resolver=location_resolver
    )
    
    # Sample activities
    activities = [
        {"id": "P1", "title": "Direct Coords", "location": {"coordinates": None}},
        {"id": "P2", "title": "Fallback API", "location": {"coordinates": None}},
        {"id": "P3", "title": "No Location", "location": {"coordinates": None}}
    ]
    
    # P1: Has coords in logistics (Direct)
    mock_p1 = {
        "productCode": "P1",
        "logistics": {
            "start": [{"location": {"ref": "LOC_1", "lat": 48.1, "lon": 2.1}}]
        }
    }
    
    # P2: Has ref only (Fallback)
    mock_p2 = {
        "productCode": "P2",
        "logistics": {
            "start": [{"location": {"ref": "LOC_2"}}]
        }
    }
    
    # P3: Has nothing
    mock_p3 = {
        "productCode": "P3",
        "logistics": {}
    }
    
    # Mock calls
    async def get_details(code, language="en"):
        if code == "P1": return mock_p1
        if code == "P2": return mock_p2
        if code == "P3": return mock_p3
        return {}
        
    service.viator_products.get_product_details.side_effect = get_details

    # Mock Bulk Location API (Only called for LOC_2)
    mock_bulk_response = [
        {
            "reference": "LOC_2",
            "center": {"latitude": 51.5, "longitude": -0.1}
        }
    ]
    service.viator_client.get_bulk_locations.return_value = mock_bulk_response

    print("Running comprehensive enrichment validation...")
    await service._enrich_activities_with_locations(activities)

    # Verify Results
    print("\n--- Validation Results ---")
    
    # P1 Validation
    p1_coords = activities[0]["location"]["coordinates"]
    pass_p1 = p1_coords == {"lat": 48.1, "lon": 2.1}
    print(f"Scenario 1 (Direct Extraction): {'[PASS]' if pass_p1 else '[FAIL]'} - Got {p1_coords}")
    
    # P2 Validation
    p2_coords = activities[1]["location"]["coordinates"]
    pass_p2 = p2_coords == {"lat": 51.5, "lon": -0.1}
    print(f"Scenario 2 (API Fallback):      {'[PASS]' if pass_p2 else '[FAIL]'} - Got {p2_coords}")
    
    # P3 Validation
    p3_coords = activities[2]["location"]["coordinates"]
    pass_p3 = p3_coords is None
    print(f"Scenario 3 (No Data):           {'[PASS]' if pass_p3 else '[FAIL]'} - Got {p3_coords}")

if __name__ == "__main__":
    asyncio.run(test_enrichment())
