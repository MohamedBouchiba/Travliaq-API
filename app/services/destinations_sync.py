"""Service for synchronizing Viator destinations to MongoDB."""

from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.viator.destinations import ViatorDestinationsService
from app.repositories.destinations_repository import DestinationsRepository

logger = logging.getLogger(__name__)


class DestinationsSyncService:
    """Service for syncing Viator destinations to MongoDB."""

    # Mapping of Viator destination types to our internal types
    DESTINATION_TYPE_MAPPING = {
        "CITY": "city",
        "COUNTRY": "country",
        "REGION": "region",
        "CONTINENT": "continent",
        "NEIGHBORHOOD": "neighborhood",
        "ATTRACTION": "attraction"
    }

    # Country code mapping (ISO 3166-1 alpha-2)
    # This maps Viator parent refs to country codes
    # You can expand this as needed
    COUNTRY_CODES = {
        "79": "FR",   # France
        "184": "GB",  # United Kingdom
        "105": "IT",  # Italy
        "209": "ES",  # Spain
        "244": "US",  # United States
        "94": "NL",   # Netherlands
        "241": "AE",  # UAE
        # Add more as discovered during sync
    }

    def __init__(
        self,
        viator_destinations: ViatorDestinationsService,
        destinations_repo: DestinationsRepository
    ):
        """
        Initialize sync service.

        Args:
            viator_destinations: Viator destinations API service
            destinations_repo: MongoDB destinations repository
        """
        self.viator = viator_destinations
        self.repo = destinations_repo

    async def sync_all_destinations(
        self,
        language: str = "en",
        filter_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sync all destinations from Viator API to MongoDB.

        Args:
            language: Language for destination names
            filter_types: Optional list of destination types to sync (e.g., ["CITY"])
                         If None, syncs all types

        Returns:
            Dictionary with sync statistics:
            {
                "total_fetched": int,
                "inserted": int,
                "updated": int,
                "skipped": int,
                "errors": int,
                "duration_seconds": float
            }
        """
        start_time = datetime.utcnow()
        stats = {
            "total_fetched": 0,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "by_type": {}
        }

        try:
            # Fetch all destinations from Viator
            logger.info("Starting destinations sync from Viator API...")
            viator_destinations = await self.viator.get_all_destinations(language=language)
            stats["total_fetched"] = len(viator_destinations)

            logger.info(f"Fetched {stats['total_fetched']} destinations from Viator")

            # First pass: Build parent lookup for country codes
            parent_lookup = self._build_parent_lookup(viator_destinations)

            # Second pass: Process each destination
            for viator_dest in viator_destinations:
                dest_type = viator_dest.get("destinationType", "UNKNOWN")

                # Filter by type if specified
                if filter_types and dest_type not in filter_types:
                    stats["skipped"] += 1
                    continue

                # Track by type
                if dest_type not in stats["by_type"]:
                    stats["by_type"][dest_type] = {"inserted": 0, "updated": 0}

                try:
                    # Transform Viator destination to our schema
                    destination_doc = self._transform_destination(
                        viator_dest,
                        parent_lookup
                    )

                    # Upsert to MongoDB
                    result = await self.repo.upsert_destination(
                        destination_id=destination_doc["destination_id"],
                        destination_data=destination_doc
                    )

                    # Note: MongoDB update_one doesn't tell us if it was insert/update
                    # We'll just count as updated for now
                    stats["updated"] += 1
                    stats["by_type"][dest_type]["updated"] += 1

                except Exception as e:
                    logger.error(
                        f"Error processing destination {viator_dest.get('ref')}: {e}",
                        exc_info=True
                    )
                    stats["errors"] += 1

            # Calculate duration
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            stats["duration_seconds"] = duration

            logger.info(
                f"Destinations sync completed: "
                f"{stats['updated']} synced, {stats['skipped']} skipped, "
                f"{stats['errors']} errors in {duration:.1f}s"
            )

            return stats

        except Exception as e:
            logger.error(f"Destinations sync failed: {e}", exc_info=True)
            raise

    def _build_parent_lookup(
        self,
        destinations: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Build a lookup dictionary of destinations by ref."""
        return {dest["ref"]: dest for dest in destinations if "ref" in dest}

    def _transform_destination(
        self,
        viator_dest: Dict[str, Any],
        parent_lookup: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Transform Viator destination to our MongoDB schema.

        Args:
            viator_dest: Destination from Viator API
            parent_lookup: Lookup dict for parent destinations

        Returns:
            Destination document for MongoDB
        """
        dest_id = viator_dest["ref"]
        dest_type = viator_dest.get("destinationType", "UNKNOWN")
        parent_ref = viator_dest.get("parentRef")

        # Determine country code
        country_code = self._determine_country_code(
            dest_type,
            dest_id,
            parent_ref,
            parent_lookup
        )

        # Extract coordinates if available
        location = None
        lat = viator_dest.get("latitude")
        lon = viator_dest.get("longitude")
        if lat is not None and lon is not None:
            location = {
                "type": "Point",
                "coordinates": [float(lon), float(lat)]
            }

        # Build document
        doc = {
            "destination_id": dest_id,
            "name": viator_dest.get("name", ""),
            "slug": viator_dest.get("lookupId", "").lower(),
            "type": self.DESTINATION_TYPE_MAPPING.get(dest_type, "unknown"),
            "viator_type": dest_type,
            "country_code": country_code,
            "parent_id": parent_ref,
            "timezone": viator_dest.get("timeZone"),
            "location": location,
            "metadata": {
                "synced_at": datetime.utcnow(),
                "source": "viator_api"
            }
        }

        # Add parent name if available
        if parent_ref and parent_ref in parent_lookup:
            parent = parent_lookup[parent_ref]
            doc["country_name"] = parent.get("name")

        return doc

    def _determine_country_code(
        self,
        dest_type: str,
        dest_id: str,
        parent_ref: Optional[str],
        parent_lookup: Dict[str, Dict[str, Any]]
    ) -> Optional[str]:
        """
        Determine country code for a destination.

        Args:
            dest_type: Type of destination
            dest_id: Destination ID
            parent_ref: Parent destination ref
            parent_lookup: Lookup for parent destinations

        Returns:
            ISO 3166-1 alpha-2 country code or None
        """
        # If it's a country, try to map the ID
        if dest_type == "COUNTRY" and dest_id in self.COUNTRY_CODES:
            return self.COUNTRY_CODES[dest_id]

        # Otherwise, look up the parent
        if parent_ref:
            # If parent is a known country
            if parent_ref in self.COUNTRY_CODES:
                return self.COUNTRY_CODES[parent_ref]

            # Recursively check parent's parent
            if parent_ref in parent_lookup:
                parent = parent_lookup[parent_ref]
                parent_parent_ref = parent.get("parentRef")
                if parent_parent_ref in self.COUNTRY_CODES:
                    return self.COUNTRY_CODES[parent_parent_ref]

        return None

    async def sync_cities_only(self, language: str = "en") -> Dict[str, Any]:
        """
        Convenience method to sync only cities.

        Args:
            language: Language for destination names

        Returns:
            Sync statistics
        """
        return await self.sync_all_destinations(
            language=language,
            filter_types=["CITY"]
        )
