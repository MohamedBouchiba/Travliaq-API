"""Test script for Viator taxonomy sync."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.services.viator.client import ViatorClient
from app.services.viator.taxonomy import ViatorTaxonomyService
from app.repositories.tags_repository import TagsRepository
from app.services.taxonomy_sync import TaxonomySyncService


async def main():
    """Test taxonomy sync."""
    print("=" * 80)
    print("Viator Taxonomy Sync Test")
    print("=" * 80)

    # Get environment variables
    viator_api_key = os.getenv("VIATOR_API_KEY_DEV")
    viator_env = os.getenv("VIATOR_ENV", "dev")
    viator_base_url = os.getenv("VIATOR_BASE_URL", "https://api.viator.com/partner")
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_db = os.getenv("MONGODB_DB", "poi_db")
    tags_collection_name = os.getenv("MONGODB_COLLECTION_TAGS", "tags")

    if not viator_api_key:
        print("ERROR: VIATOR_API_KEY_DEV not set in environment")
        sys.exit(1)

    print(f"\nConfiguration:")
    print(f"  Viator API Key: {viator_api_key[:10]}...")
    print(f"  Viator Env: {viator_env}")
    print(f"  Viator Base URL: {viator_base_url}")
    print(f"  MongoDB URI: {mongodb_uri}")
    print(f"  MongoDB DB: {mongodb_db}")
    print(f"  Tags Collection: {tags_collection_name}")

    # Initialize services
    print("\n" + "=" * 80)
    print("Initializing services...")
    print("=" * 80)

    # MongoDB
    mongo_client = AsyncIOMotorClient(mongodb_uri)
    db = mongo_client[mongodb_db]
    tags_collection = db[tags_collection_name]

    # Viator client
    viator_client = ViatorClient(
        api_key=viator_api_key,
        base_url=viator_base_url,
        environment=viator_env
    )

    # Create services
    viator_taxonomy = ViatorTaxonomyService(viator_client)
    tags_repo = TagsRepository(tags_collection)
    sync_service = TaxonomySyncService(viator_taxonomy, tags_repo)

    # Create indexes
    print("\nCreating MongoDB indexes...")
    await tags_repo.create_indexes()
    print("✓ Indexes created")

    # Sync tags
    print("\n" + "=" * 80)
    print("Syncing tags from Viator API...")
    print("=" * 80)

    stats = await sync_service.sync_all_tags(language="en")

    print("\n" + "=" * 80)
    print("Sync Results:")
    print("=" * 80)
    print(f"  Total fetched: {stats['total_fetched']}")
    print(f"  Updated: {stats['updated']}")
    print(f"  Errors: {stats['errors']}")
    print(f"  Root tags: {stats['root_tags']}")
    print(f"  Child tags: {stats['child_tags']}")
    print(f"  Started: {stats['started_at']}")
    print(f"  Completed: {stats['completed_at']}")

    # Test category mapping
    print("\n" + "=" * 80)
    print("Testing Dynamic Category Mapping...")
    print("=" * 80)

    test_categories = ["food", "museum", "art", "tours", "water", "adventure"]

    for category in test_categories:
        tags = await tags_repo.find_tags_by_category_keyword(category, language="en")
        tag_ids = [tag["tag_id"] for tag in tags]
        tag_names = [tag["tag_name"] for tag in tags[:5]]  # First 5

        print(f"\n  Category: '{category}'")
        print(f"    Found {len(tags)} matching tags")
        print(f"    Tag IDs: {tag_ids[:10]}")  # First 10
        if tag_names:
            print(f"    Tag Names: {tag_names}")

    # Show some root tags
    print("\n" + "=" * 80)
    print("Sample Root Tags:")
    print("=" * 80)

    root_tags = await tags_repo.get_all_root_tags()
    for tag in root_tags[:10]:
        print(f"  [{tag['tag_id']}] {tag['tag_name']}")
        # Show translations if available
        all_names = tag.get("all_names", {})
        if len(all_names) > 1:
            print(f"       Translations: {dict(list(all_names.items())[:3])}")

    print("\n" + "=" * 80)
    print("✓ Test Complete!")
    print("=" * 80)

    # Close connections
    mongo_client.close()
    await viator_client.close()


if __name__ == "__main__":
    asyncio.run(main())
