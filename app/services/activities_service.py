"""Business logic service for activities."""

from __future__ import annotations
import hashlib
import json
import asyncio
import logging
from typing import Optional
from datetime import datetime

from app.services.viator.client import ViatorClient
from app.services.viator.products import ViatorProductsService
from app.services.redis_cache import RedisCache
from app.services.location_resolver import LocationResolver
from app.repositories.activities_repository import ActivitiesRepository
from app.repositories.tags_repository import TagsRepository
from app.utils.viator_mapper import ViatorMapper
from app.models.activities import (
    ActivitySearchRequest,
    ActivitySearchResponse,
    SearchResults,
    LocationResolution,
    CacheInfo
)
from app.core.constants import SORT_MAPPING

logger = logging.getLogger(__name__)


class ActivitiesService:
    """Business logic for activities search and management."""

    def __init__(
        self,
        viator_client: ViatorClient,
        viator_products: ViatorProductsService,
        redis_cache: RedisCache,
        activities_repo: ActivitiesRepository,
        tags_repo: TagsRepository,
        location_resolver: LocationResolver,
        cache_ttl: int = 604800  # 7 days
    ):
        self.viator_client = viator_client
        self.viator_products = viator_products
        self.cache = redis_cache
        self.repo = activities_repo
        self.tags_repo = tags_repo
        self.location_resolver = location_resolver
        self.cache_ttl = cache_ttl

    async def search_activities(self, request: ActivitySearchRequest) -> ActivitySearchResponse:
        """
        Search activities with caching and persistence.

        Flow:
        1. Resolve location (city/geo → destination_id)
        2. Check Redis cache
        3. If miss → Call Viator API
        4. Transform response (simplify)
        5. Cache in Redis + persist in MongoDB
        6. Return simplified response

        Args:
            request: Activity search request

        Returns:
            Activity search response
        """
        # 1. Resolve location
        destination_id, matched_location = await self._resolve_location(request.location)

        if not destination_id:
            raise ValueError(f"Could not resolve location: {request.location}")

        logger.info(f"Resolved location to destination ID: {destination_id}")

        # 2. Check cache
        cache_key = self._build_cache_key(destination_id, request)
        cached = self.cache.get("activities_search", {"key": cache_key})

        if cached:
            logger.info(f"Cache HIT for activities search")
            return ActivitySearchResponse(
                success=True,
                location=matched_location,
                filters_applied=self._build_filters_summary(request),
                results=SearchResults(**cached["results"]),
                cache_info=CacheInfo(
                    cached=True,
                    cached_at=cached.get("cached_at"),
                    expires_at=cached.get("expires_at")
                )
            )

        logger.info(f"Cache MISS for activities search")

        # 3. Call Viator API
        viator_response = await self._call_viator_search(destination_id, request)

        # 4. Transform response
        activities = [
            ViatorMapper.map_product_summary(product)
            for product in viator_response.get("products", [])
        ]
        
        # 4.5 Enrich with locations (New Step)
        await self._enrich_activities_with_locations(activities, language=request.language)

        # 5. Persist in MongoDB (async, non-blocking)
        await self._persist_activities(activities)

        # 6. Cache results
        results = SearchResults(
            total=viator_response.get("totalCount", 0),
            page=request.pagination.page,
            limit=request.pagination.limit,
            activities=activities
        )

        cache_data = {
            "results": results.model_dump(),
            "cached_at": datetime.utcnow().isoformat(),
            "expires_at": datetime.utcnow().isoformat()  # Compute expiration
        }

        self.cache.set("activities_search", {"key": cache_key}, cache_data, ttl_seconds=self.cache_ttl)

        return ActivitySearchResponse(
            success=True,
            location=matched_location,
            filters_applied=self._build_filters_summary(request),
            results=results,
            cache_info=CacheInfo(
                cached=False,
                cached_at=None,
                expires_at=None
            )
        )

    async def _resolve_location(self, location) -> tuple[Optional[str], LocationResolution]:
        """Resolve location input to Viator destination ID."""
        # Option 1: Direct destination_id
        if location.destination_id:
            return location.destination_id, LocationResolution(
                matched_city=None,
                destination_id=location.destination_id,
                coordinates=None
            )

        # Option 2: City name
        if location.city:
            result = await self.location_resolver.resolve_city(
                location.city,
                location.country_code
            )
            if result:
                dest_id, matched_city, score = result
                return dest_id, LocationResolution(
                    matched_city=matched_city,
                    destination_id=dest_id,
                    coordinates=None,
                    match_score=score
                )

        # Option 3: Geo coordinates
        if location.geo:
            geo = location.geo
            result = await self.location_resolver.resolve_geo(
                geo.lat,
                geo.lon,
                geo.radius_km
            )
            if result:
                dest_id, city_name, distance_km = result
                return dest_id, LocationResolution(
                    matched_city=city_name,
                    destination_id=dest_id,
                    coordinates={"lat": geo.lat, "lon": geo.lon},
                    distance_km=distance_km
                )

        return None, LocationResolution(destination_id="", matched_city=None)

    async def _call_viator_search(self, destination_id: str, request: ActivitySearchRequest) -> dict:
        """Call Viator products search API."""
        # Map simple categories to Viator tags dynamically from MongoDB
        tags = await self._map_categories_to_tags(
            request.filters.categories if request.filters else [],
            language=request.language
        )

        # Build filters
        kwargs = {
            "destination_id": destination_id,
            "start_date": request.dates.start.isoformat(),
            "end_date": request.dates.end.isoformat() if request.dates.end else None,
            "tags": tags if tags else None,
            "currency": request.currency,
            "language": request.language,
        }

        # Add optional filters
        if request.filters:
            if request.filters.price_range:
                kwargs["lowest_price"] = request.filters.price_range.min
                kwargs["highest_price"] = request.filters.price_range.max
            if request.filters.rating_min:
                kwargs["rating_from"] = request.filters.rating_min
            if request.filters.flags:
                kwargs["flags"] = request.filters.flags

        # Add sorting
        if request.sorting:
            kwargs["sort"] = SORT_MAPPING.get(request.sorting.sort_by.value, "DEFAULT")
            kwargs["order"] = "DESCENDING" if request.sorting.order.value == "desc" else "ASCENDING"

        # Add pagination
        start = (request.pagination.page - 1) * request.pagination.limit + 1
        kwargs["start"] = start
        kwargs["count"] = request.pagination.limit

        return await self.viator_products.search_products(**kwargs)

    async def _map_categories_to_tags(self, categories: Optional[list[str]], language: str = "en") -> Optional[list[int]]:
        """
        Map simplified categories to Viator tag IDs dynamically from MongoDB.

        NO hardcoded mappings - searches MongoDB tags collection for matching tags.

        Args:
            categories: List of category keywords (e.g., ['food', 'museum'])
            language: Language code for searching

        Returns:
            List of Viator tag IDs or None
        """
        if not categories:
            return None

        tags = []
        for category in categories:
            # Search MongoDB for tags matching this category keyword
            matching_tags = await self.tags_repo.find_tags_by_category_keyword(
                keyword=category,
                language=language
            )

            # Extract tag IDs
            for tag in matching_tags:
                tags.append(tag["tag_id"])

            if not matching_tags:
                logger.warning(f"No tags found in MongoDB for category: '{category}'")

        return list(set(tags)) if tags else None

    async def _persist_activities(self, activities: list[dict]):
        """Persist activities to MongoDB (upsert)."""
        for activity in activities:
            try:
                await self.repo.upsert_activity(activity["id"], activity)
            except Exception as e:
                logger.error(f"Error persisting activity {activity['id']}: {e}")

    async def _enrich_activities_with_locations(self, activities: list[dict], language: str = "en"):
        """
        Enrich activities with location coordinates using Viator bulk endpoints.

        Flow:
        1. Extract product codes from activities lacking coordinates
        2. Bulk fetch product details to get location references (logistics/itinerary)
        3. Bulk fetch location details to get lat/lon
        4. Match back to activities
        """
        if not activities:
            return

        # Filter activities that need location enrichment (missing coordinates)
        candidates = [
            a for a in activities 
            if not a.get("location", {}).get("coordinates")
        ]
        
        if not candidates:
            return

        product_codes = [a["id"] for a in candidates]
        
        try:
            logger.info(f"[ENRICH] Attempting to enrich {len(candidates)} activities")
            
            # Step 1: Bulk fetch product details to get location refs
            # Note: /products/bulk returns 403 for some keys, so we fallback to parallel individual fetches
            # products_details = await self.viator_products.get_bulk_products(product_codes, language=language)
            
            logger.info(f"[ENRICH] Fetching details for {len(product_codes)} products in parallel")
            tasks = [
                self.viator_products.get_product_details(code, language=language)
                for code in product_codes
            ]
            products_details = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_details = []
            for res in products_details:
                if isinstance(res, Exception):
                    logger.warning(f"[ENRICH] Failed to fetch product details: {res}")
                elif res:
                    valid_details.append(res)
            
            products_details = valid_details
            logger.info(f"[ENRICH] Fetched {len(products_details)} product details")
            
            # Map product_code -> location_refs AND resolved coords
            product_refs_map = {}
            resolved_coords_map = {} # Key: ref -> coords
            product_direct_coords_map = {} # Key: product_code -> coords (for locs with no ref)
            all_refs_to_fetch = set()
            
            for prod in products_details:
                # NEW: Extract full location info (ref + coords)
                locs = ViatorMapper.extract_product_locations(prod)
                
                # Store refs for potential lookup
                refs = [l["ref"] for l in locs if l["ref"]]
                if refs:
                    product_refs_map[prod["productCode"]] = refs
                
                # Check directly extracted coords
                for loc in locs:
                    coords = None
                    if loc["lat"] and loc["lon"]:
                        coords = {"lat": loc["lat"], "lon": loc["lon"]}
                    
                    if coords:
                        if loc["ref"]:
                            resolved_coords_map[loc["ref"]] = coords
                        elif prod["productCode"] not in product_direct_coords_map:
                            # If no ref but have coords, assign to product directly (first one wins)
                            product_direct_coords_map[prod["productCode"]] = coords
                    elif loc["ref"]:
                        # No coords, but have ref -> needs fetch
                        all_refs_to_fetch.add(loc["ref"])

            # Filter out refs we already resolved locally
            refs_needed = [r for r in all_refs_to_fetch if r not in resolved_coords_map]
            
            logger.info(f"[ENRICH] Resolved {len(resolved_coords_map)} refs locally + {len(product_direct_coords_map)} direct products. Need to fetch {len(refs_needed)} refs.")

            if refs_needed:
                # Step 2: Bulk fetch location details to get coordinates (only for missing ones)
                # We use the corrected endpoint /partner/locations/bulk via get_bulk_locations
                logger.info(f"[ENRICH] Fetching details for {len(refs_needed)} locations via bulk API")
                try:
                    locations_details = await self.viator_client.get_bulk_locations(list(refs_needed))
                    logger.info(f"[ENRICH] Fetched {len(locations_details)} location details from API")
                    
                    for loc in locations_details:
                        # Check for direct center
                        center = loc.get("center")
                        if not center and "location" in loc:
                            center = loc["location"].get("center")
                        
                        if center:
                            resolved_coords_map[loc["reference"]] = {
                                "lat": center.get("latitude"),
                                "lon": center.get("longitude")
                            }
                except Exception as e:
                    logger.error(f"[ENRICH] Bulk location fetch failed: {e}")
                    # Fallback or just continue with what we have

            
            logger.info(f"[ENRICH] Total mapped locations: {len(resolved_coords_map)}")
            
            # Step 3: Assign coordinates to activities
            enriched_count = 0
            for activity in candidates:
                p_code = activity["id"]
                
                # 1. Check direct product coords (highest priority if specific to this product)
                direct_coords = product_direct_coords_map.get(p_code)
                if direct_coords:
                    activity["location"]["coordinates"] = direct_coords
                    logger.info(f"Enriched activity {p_code} with direct coordinates: {direct_coords}")
                    enriched_count += 1
                    continue

                # 2. Check via Refs
                refs = product_refs_map.get(p_code, [])
                for ref in refs:
                    coords = resolved_coords_map.get(ref)
                    if coords:
                        activity["location"]["coordinates"] = coords
                        logger.info(f"Enriched activity {p_code} with ref-resolved coordinates: {coords}")
                        enriched_count += 1
                        break
            
            logger.info(f"[ENRICH] Total enriched: {enriched_count}/{len(candidates)}")
            

                        
        except Exception as e:
            logger.error(f"Error enriching activities with locations: {e}", exc_info=True)
            # Don't fail the search if enrichment fails
            pass

    def _build_cache_key(self, destination_id: str, request: ActivitySearchRequest) -> str:
        """Build unique cache key for search request."""
        filters_dict = request.filters.model_dump() if request.filters else {}
        filters_str = json.dumps(filters_dict, sort_keys=True)
        filters_hash = hashlib.md5(filters_str.encode()).hexdigest()[:8]

        end_date = request.dates.end.isoformat() if request.dates.end else "none"

        return f"{destination_id}:{request.dates.start.isoformat()}:{end_date}:{filters_hash}"

    def _build_filters_summary(self, request: ActivitySearchRequest) -> dict:
        """Build summary of applied filters for response."""
        summary = {}

        if request.filters:
            if request.filters.categories:
                summary["categories"] = request.filters.categories
            if request.filters.price_range:
                summary["price_range"] = request.filters.price_range.model_dump()
            if request.filters.rating_min:
                summary["rating_min"] = request.filters.rating_min

        return summary
