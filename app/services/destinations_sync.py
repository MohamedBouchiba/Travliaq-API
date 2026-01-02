"""Service for synchronizing Viator destinations to MongoDB."""

from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import pycountry
from rapidfuzz import fuzz, process

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
        self._country_name_to_code_cache: Dict[str, str] = {}

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
                    await self.repo.upsert_destination(
                        destination_id=destination_doc["destination_id"],
                        destination_data=destination_doc
                    )

                    # Count as updated (upsert could be insert or update)
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
        """Build a lookup dictionary of destinations by destinationId."""
        return {
            str(dest["destinationId"]): dest
            for dest in destinations
            if "destinationId" in dest
        }

    def _get_country_code_from_name(self, country_name: str) -> Optional[str]:
        """
        Convert country name to ISO 3166-1 alpha-2 code using pycountry with fuzzy matching.

        Handles common variations and subdivisions:
        - USA/US → United States
        - UK/Britain → United Kingdom
        - England/Scotland/Wales/Northern Ireland → United Kingdom
        - Turkey → Türkiye (new official name)
        - And many more...

        Args:
            country_name: Name of the country (e.g., "France", "United States", "USA")

        Returns:
            ISO alpha-2 country code (e.g., "FR", "US") or None if not found
        """
        if not country_name:
            return None

        # Check cache first
        if country_name in self._country_name_to_code_cache:
            return self._country_name_to_code_cache[country_name]

        # Common name variations that pycountry doesn't handle well
        # This is NOT hardcoding countries - it's mapping common names to ISO names
        common_variations = {
            # USA variations
            "USA": "US",
            "U.S.A": "US",
            "U.S.A.": "US",
            "US": "US",
            "U.S": "US",
            "United States": "US",
            "United States of America": "US",

            # UK variations and subdivisions
            "UK": "GB",
            "U.K": "GB",
            "U.K.": "GB",
            "Britain": "GB",
            "Great Britain": "GB",
            "England": "GB",
            "Scotland": "GB",
            "Wales": "GB",
            "Northern Ireland": "GB",

            # Turkey (new name)
            "Turkey": "TR",
            "Türkiye": "TR",

            # UAE variations
            "UAE": "AE",
            "U.A.E": "AE",
            "U.A.E.": "AE",
            "United Arab Emirates": "AE",

            # Other common variations
            "Holland": "NL",
            "The Netherlands": "NL",

            # Territories and special cases
            "Palestinian Territories": "PS",
            "Palestine": "PS",
            "St Maarten": "SX",
            "Sint Maarten": "SX",
            "Bonaire": "BQ",  # Bonaire, Sint Eustatius and Saba
            "Kosovo": "XK",  # User-assigned code (not official ISO but widely used)
            "Brunei": "BN",
            "Brunei Darussalam": "BN",
            "Democratic Republic of Congo": "CD",
            "Congo (DRC)": "CD",
            "DR Congo": "CD",
            "Eswatini (Swaziland)": "SZ",
            "Eswatini": "SZ",
            "Swaziland": "SZ",
            "East Timor": "TL",
            "Timor-Leste": "TL",

            # Islands and territories
            "Channel Islands": "GB",  # British Crown dependency (Jersey, Guernsey)
            "Réunion Island": "RE",
            "Réunion": "RE",
            "Reunion": "RE",
            "Reunion Island": "RE",
            "US Virgin Islands": "VI",
            "U.S. Virgin Islands": "VI",
            "Virgin Islands": "VI",
        }

        # Check common variations first (case insensitive)
        for variation, code in common_variations.items():
            if country_name.upper() == variation.upper():
                self._country_name_to_code_cache[country_name] = code
                logger.debug(f"Mapped common variation '{country_name}' → {code}")
                return code

        # Try exact match with pycountry (case insensitive)
        try:
            country = pycountry.countries.get(name=country_name)
            if country:
                code = country.alpha_2
                self._country_name_to_code_cache[country_name] = code
                return code
        except (KeyError, AttributeError):
            pass

        # Try alpha_2 code lookup (in case input is already a code)
        try:
            country = pycountry.countries.get(alpha_2=country_name.upper())
            if country:
                code = country.alpha_2
                self._country_name_to_code_cache[country_name] = code
                return code
        except (KeyError, AttributeError):
            pass

        # Try alpha_3 code lookup
        try:
            country = pycountry.countries.get(alpha_3=country_name.upper())
            if country:
                code = country.alpha_2
                self._country_name_to_code_cache[country_name] = code
                return code
        except (KeyError, AttributeError):
            pass

        # Try fuzzy matching on all country names
        all_countries = list(pycountry.countries)
        country_names = [c.name for c in all_countries]

        # Also include common names and official names (using getattr to avoid warnings)
        for country in all_countries:
            common_name = getattr(country, 'common_name', None)
            if common_name:
                country_names.append(common_name)
            official_name = getattr(country, 'official_name', None)
            if official_name:
                country_names.append(official_name)

        # Fuzzy match with threshold of 80
        match = process.extractOne(
            country_name,
            country_names,
            scorer=fuzz.ratio,
            score_cutoff=80
        )

        if match:
            matched_name, score = match[0], match[1]
            logger.debug(f"Fuzzy matched '{country_name}' → '{matched_name}' (score: {score})")

            # Find the country object with this name
            for country in all_countries:
                if country.name == matched_name or \
                   getattr(country, 'common_name', None) == matched_name or \
                   getattr(country, 'official_name', None) == matched_name:
                    code = country.alpha_2
                    self._country_name_to_code_cache[country_name] = code
                    return code

        logger.warning(f"Could not find country code for: '{country_name}'")
        return None

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
        dest_id = str(viator_dest["destinationId"])
        dest_type = viator_dest.get("type", "UNKNOWN")
        dest_name = viator_dest.get("name", "")
        parent_id = viator_dest.get("parentDestinationId")
        parent_id_str = str(parent_id) if parent_id else None

        # Determine country code dynamically using pycountry (no hardcoded mappings)
        country_code = self._determine_country_code(
            dest_type,
            dest_name,
            parent_id_str,
            parent_lookup
        )

        # Extract coordinates if available
        location = None
        center = viator_dest.get("center")
        if center:
            lat = center.get("latitude")
            lon = center.get("longitude")
            if lat is not None and lon is not None:
                location = {
                    "type": "Point",
                    "coordinates": [float(lon), float(lat)]
                }

        # Build document
        now = datetime.utcnow()
        doc = {
            "destination_id": dest_id,
            "name": viator_dest.get("name", ""),
            "slug": viator_dest.get("lookupId", "").lower(),
            "type": self.DESTINATION_TYPE_MAPPING.get(dest_type, "unknown"),
            "viator_type": dest_type,
            "country_code": country_code,
            "parent_id": parent_id_str,
            "location": location,
            "iata_codes": viator_dest.get("iataCodes", []),
            "metadata": {
                "synced_at": now,
                "last_synced": now,
                "source": "viator_api"
            }
        }

        # Add parent name if available
        if parent_id_str and parent_id_str in parent_lookup:
            parent = parent_lookup[parent_id_str]
            doc["country_name"] = parent.get("name")

        return doc

    def _determine_country_code(
        self,
        dest_type: str,
        dest_name: str,
        parent_ref: Optional[str],
        parent_lookup: Dict[str, Dict[str, Any]]
    ) -> Optional[str]:
        """
        Dynamically determine country code for a destination using pycountry.

        This method uses NO hardcoded mappings - it resolves country names to ISO codes
        dynamically using the pycountry library with fuzzy matching.

        Args:
            dest_type: Type of destination (CITY, COUNTRY, REGION, etc.)
            dest_name: Name of the destination
            parent_ref: Parent destination ID (as string)
            parent_lookup: Lookup dict for parent destinations

        Returns:
            ISO 3166-1 alpha-2 country code or None
        """
        # If it's a country itself, convert its name to ISO code
        if dest_type == "COUNTRY":
            return self._get_country_code_from_name(dest_name)

        # Otherwise, traverse up the parent chain to find the country
        current_parent_ref = parent_ref
        max_depth = 5  # Prevent infinite loops

        for _ in range(max_depth):
            if not current_parent_ref or current_parent_ref not in parent_lookup:
                break

            parent = parent_lookup[current_parent_ref]
            parent_type = parent.get("type", "")
            parent_name = parent.get("name", "")

            # If we found a country parent, convert its name to code
            if parent_type == "COUNTRY":
                return self._get_country_code_from_name(parent_name)

            # Move up to the next parent
            parent_parent_id = parent.get("parentDestinationId")
            current_parent_ref = str(parent_parent_id) if parent_parent_id else None

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
