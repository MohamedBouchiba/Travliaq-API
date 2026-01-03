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
from app.services.geoapify import GeoapifyClient
from app.services.google_places import GooglePlacesClient
from app.services.translation import TranslationClient
from app.repositories.activities_repository import ActivitiesRepository
from app.repositories.tags_repository import TagsRepository
from app.repositories.attractions_repository import AttractionsRepository
from app.repositories.geocoding_cache_repository import GeocodingCacheRepository
from app.utils.viator_mapper import ViatorMapper
from app.utils.coordinate_dispersion import generate_dispersed_coordinates
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
        viator_attractions,  # ViatorAttractionsService
        redis_cache: RedisCache,
        activities_repo: ActivitiesRepository,
        tags_repo: TagsRepository,
        attractions_repo: AttractionsRepository,
        geocoding_cache_repo: GeocodingCacheRepository,
        location_resolver: LocationResolver,
        geoapify_client: Optional[GeoapifyClient] = None,
        google_places_client: Optional[GooglePlacesClient] = None,
        translation_client: Optional[TranslationClient] = None,
        enable_geocoding: bool = False,
        cache_ttl: int = 604800  # 7 days
    ):
        self.viator_client = viator_client
        self.viator_products = viator_products
        self.viator_attractions = viator_attractions
        self.cache = redis_cache
        self.repo = activities_repo
        self.tags_repo = tags_repo
        self.attractions_repo = attractions_repo
        self.geocoding_cache_repo = geocoding_cache_repo
        self.location_resolver = location_resolver
        self.geoapify_client = geoapify_client
        self.google_places_client = google_places_client
        self.translation_client = translation_client
        self.enable_geocoding = enable_geocoding
        self.cache_ttl = cache_ttl

    async def search_activities(self, request: ActivitySearchRequest, force_refresh: bool = False) -> ActivitySearchResponse:
        """
        Search activities with caching and persistence.

        Flow:
        1. Resolve location (city/geo → destination_id)
        2. Check Redis cache (unless force_refresh=True)
        3. If miss → Call Viator API
        4. Transform response (simplify)
        5. Cache in Redis + persist in MongoDB
        6. Return simplified response

        Args:
            request: Activity search request
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Activity search response
        """
        logger.info(f"=== ACTIVITIES SEARCH STARTED === mode={request.search_mode.value} force_refresh={force_refresh}")

        # 1. Resolve location
        destination_id, matched_location = await self._resolve_location(request.location)

        if not destination_id:
            raise ValueError(f"Could not resolve location: {request.location}")

        logger.info(f"Resolved location to destination ID: {destination_id}")

        # 2. Check cache (unless force_refresh)
        cache_key = self._build_cache_key(destination_id, request)

        if not force_refresh:
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
        else:
            logger.info(f"FORCE REFRESH requested - bypassing cache")

        logger.info(f"Cache MISS for activities search")

        # 3. Call Viator API (conditional based on search_mode)
        from app.models.activities import SearchMode

        if request.search_mode == SearchMode.BOTH:
            # UNIFIED SEARCH: Fetch both activities and attractions in parallel
            logger.info(f"[UNIFIED] Fetching BOTH activities AND attractions for destination {destination_id}")
            activities, total_count = await self._search_unified(destination_id, request)

        elif request.search_mode == SearchMode.ATTRACTIONS:
            # ATTRACTIONS ONLY
            logger.info(f"Searching ATTRACTIONS for destination {destination_id}")

            viator_response = await self.viator_attractions.search_attractions(
                destination_id=destination_id,
                sort=request.sorting.sort_by.value.upper() if request.sorting and request.sorting.sort_by.value != "default" else "DEFAULT",
                start=(request.pagination.page - 1) * request.pagination.limit + 1,
                count=request.pagination.limit,
                language=request.language
            )

            activities = [
                ViatorMapper.map_attraction(attraction)
                for attraction in viator_response.get("attractions", [])
            ]
            total_count = viator_response.get("totalCount", 0)

            # Set type field for consistency
            for activity in activities:
                activity["type"] = "attraction"

            logger.info(f"Transformed {len(activities)} attractions from Viator response")

        else:  # SearchMode.ACTIVITIES (default)
            # ACTIVITIES ONLY
            logger.info(f"Searching ACTIVITIES for destination {destination_id}")

            viator_response = await self._call_viator_search(destination_id, request)

            activities = [
                ViatorMapper.map_product_summary(product)
                for product in viator_response.get("products", [])
            ]
            total_count = viator_response.get("totalCount", 0)

            # Set type field for consistency
            for activity in activities:
                activity["type"] = "activity"

            logger.info(f"Transformed {len(activities)} activities from Viator response")

            # Enrich with locations (ONLY for activities)
            logger.info(f"Starting location enrichment for {len(activities)} activities...")
            await self._enrich_activities_with_locations(activities, language=request.language)
            logger.info(f"Location enrichment completed")

        # 4. Resolve tag IDs to names (for all types)
        logger.info(f"Resolving tag names for {len(activities)} items...")
        await self._resolve_tag_names(activities, language=request.language)
        logger.info(f"Tag resolution completed")

        # 4.5 Apply geo filtering if geo search was performed
        if request.location.geo:
            logger.info(f"[GEO] Applying geographic filtering and sorting...")
            activities, total_count = await self._apply_geo_filtering(
                activities=activities,
                search_coords={"lat": request.location.geo.lat, "lon": request.location.geo.lon},
                radius_km=request.location.geo.radius_km,
                original_total=total_count
            )
            logger.info(f"[GEO] After filtering: {len(activities)} activities within {request.location.geo.radius_km}km")

        # 5. Persist in MongoDB (async, non-blocking)
        await self._persist_activities(activities)

        # 6. Cache results
        results = SearchResults(
            total=total_count,
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
                coordinates=None,
                search_type="destination_id"
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
                    match_score=score,
                    search_type="city"
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
                    distance_km=distance_km,
                    search_type="geo"
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

    async def _search_unified(self, destination_id: str, request: ActivitySearchRequest) -> tuple[list[dict], int]:
        """
        Unified search: Fetch BOTH activities and attractions in parallel and merge them.

        Strategy:
        - Fetch activities (max 50) and attractions (max 30) in parallel
        - Transform both to common format
        - Merge and sort by rating
        - Apply pagination to merged results

        Args:
            destination_id: Viator destination ID
            request: Search request with filters and pagination

        Returns:
            Tuple of (merged_activities, total_count)
        """
        logger.info(f"[UNIFIED] Starting parallel fetch for destination {destination_id}")

        # Prepare parallel tasks
        async def fetch_activities():
            """Fetch and transform activities."""
            try:
                logger.info(f"[UNIFIED] Fetching activities...")
                viator_response = await self._call_viator_search(destination_id, request)

                activities = [
                    ViatorMapper.map_product_summary(product)
                    for product in viator_response.get("products", [])
                ]

                # Add type field
                for activity in activities:
                    activity["type"] = "activity"

                logger.info(f"[UNIFIED] Fetched {len(activities)} activities (total: {viator_response.get('totalCount', 0)})")

                # Enrich with locations
                await self._enrich_activities_with_locations(activities, language=request.language)

                return activities, viator_response.get("totalCount", 0)
            except Exception as e:
                logger.error(f"[UNIFIED] Error fetching activities: {e}")
                return [], 0

        async def fetch_attractions():
            """Fetch and transform attractions."""
            try:
                logger.info(f"[UNIFIED] Fetching attractions...")
                viator_response = await self.viator_attractions.search_attractions(
                    destination_id=destination_id,
                    sort="DEFAULT",
                    start=1,
                    count=30,  # Limit attractions to 30
                    language=request.language
                )

                attractions = [
                    ViatorMapper.map_attraction(attraction)
                    for attraction in viator_response.get("attractions", [])
                ]

                # Add type field
                for attraction in attractions:
                    attraction["type"] = "attraction"

                logger.info(f"[UNIFIED] Fetched {len(attractions)} attractions (total: {viator_response.get('totalCount', 0)})")

                return attractions, viator_response.get("totalCount", 0)
            except Exception as e:
                logger.error(f"[UNIFIED] Error fetching attractions: {e}")
                return [], 0

        # Execute both in parallel
        (activities, activities_total), (attractions, attractions_total) = await asyncio.gather(
            fetch_activities(),
            fetch_attractions()
        )

        # Merge results
        merged = activities + attractions

        logger.info(
            f"[UNIFIED] Merged results: {len(activities)} activities + {len(attractions)} attractions = {len(merged)} total"
        )

        # Sort by rating (descending)
        merged.sort(
            key=lambda x: x.get("rating", {}).get("average", 0),
            reverse=True
        )

        logger.info(f"[UNIFIED] Sorted {len(merged)} items by rating")

        # Apply pagination to merged results
        start_idx = (request.pagination.page - 1) * request.pagination.limit
        end_idx = start_idx + request.pagination.limit
        paginated = merged[start_idx:end_idx]

        logger.info(
            f"[UNIFIED] Pagination: page {request.pagination.page}, "
            f"showing items {start_idx+1}-{min(end_idx, len(merged))} of {len(merged)}"
        )

        # Total count is sum of both
        total_count = activities_total + attractions_total

        return paginated, total_count

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
                if locs:
                    logger.info(f"[ENRICH] Product {prod['productCode']}: extracted {len(locs)} locations")

                # Store refs for potential lookup
                refs = [l["ref"] for l in locs if l["ref"]]
                if refs:
                    product_refs_map[prod["productCode"]] = refs
                    logger.info(f"[ENRICH] Product {prod['productCode']}: refs = {refs}")
                
                # Check directly extracted coords
                for loc in locs:
                    coords = None
                    if loc["lat"] and loc["lon"]:
                        coords = {"lat": loc["lat"], "lon": loc["lon"]}

                    if coords:
                        if loc["ref"]:
                            resolved_coords_map[loc["ref"]] = coords
                            logger.info(f"[ENRICH] Found coords for ref {loc['ref']}: {coords}")
                        elif prod["productCode"] not in product_direct_coords_map:
                            # If no ref but have coords, assign to product directly (first one wins)
                            product_direct_coords_map[prod["productCode"]] = coords
                            logger.info(f"[ENRICH] Found direct coords for product {prod['productCode']}: {coords}")
                    elif loc["ref"]:
                        # No coords, but have ref -> needs fetch
                        all_refs_to_fetch.add(loc["ref"])

            # Filter out refs we already resolved locally
            refs_needed = [r for r in all_refs_to_fetch if r not in resolved_coords_map]
            
            logger.info(f"[ENRICH] Resolved {len(resolved_coords_map)} refs locally + {len(product_direct_coords_map)} direct products. Need to fetch {len(refs_needed)} refs.")

            if refs_needed:
                # Step 2: Bulk fetch location details to get coordinates (only for missing ones)
                # We use the corrected endpoint /partner/locations/bulk via get_bulk_locations
                # IMPORTANT: Viator API has a limit of 500 location refs per request
                logger.info(f"[ENRICH] Fetching details for {len(refs_needed)} locations via bulk API")

                # Chunk refs into batches of 500 (Viator API limit)
                CHUNK_SIZE = 500
                refs_chunks = [refs_needed[i:i+CHUNK_SIZE] for i in range(0, len(refs_needed), CHUNK_SIZE)]
                logger.info(f"[ENRICH] Split into {len(refs_chunks)} chunks of max {CHUNK_SIZE} refs")

                try:
                    for chunk_idx, chunk in enumerate(refs_chunks):
                        logger.info(f"[ENRICH] Fetching chunk {chunk_idx+1}/{len(refs_chunks)} ({len(chunk)} refs)")
                        locations_details = await self.viator_client.get_bulk_locations(list(chunk))
                        logger.info(f"[ENRICH] Fetched {len(locations_details)} location details from chunk {chunk_idx+1}")

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
                    activity["location"]["coordinates_precision"] = "precise"
                    logger.info(f"Enriched activity {p_code} with direct coordinates: {direct_coords}")
                    enriched_count += 1
                    continue

                # 2. Check via Refs
                refs = product_refs_map.get(p_code, [])
                for ref in refs:
                    coords = resolved_coords_map.get(ref)
                    if coords:
                        activity["location"]["coordinates"] = coords
                        activity["location"]["coordinates_precision"] = "precise"
                        logger.info(f"Enriched activity {p_code} with ref-resolved coordinates: {coords}")
                        enriched_count += 1
                        break

            logger.info(f"[ENRICH] LEVEL 1 (Viator Logistics) enriched: {enriched_count}/{len(candidates)}")

            # LEVEL 2: Attraction Matching (reverse lookup productCode → attraction)
            logger.info(f"[ENRICH] Starting LEVEL 2: Attraction Matching...")
            await self._enrich_via_attraction_matching(activities)

            # LEVEL 3: Geocoding Intelligent (Geoapify → Google Places with cache)
            logger.info(f"[ENRICH] Starting LEVEL 3: Intelligent Geocoding...")
            await self._enrich_via_geocoding(activities, language=language)

            # LEVEL 4: Intelligent Dispersion (GeoGuessr-style for remaining activities)
            logger.info(f"[ENRICH] Starting LEVEL 4: Intelligent Dispersion...")
            await self._enrich_via_dispersion(activities)

            # Log final summary
            activities_with_coords = [
                a for a in candidates
                if a.get("location", {}).get("coordinates") is not None
            ]
            logger.info(f"[ENRICH] FINAL: {len(activities_with_coords)}/{len(candidates)} activities have coordinates")

            # Count by precision level
            precision_counts = {}
            for act in activities_with_coords:
                precision = act.get("location", {}).get("coordinates_precision", "unknown")
                precision_counts[precision] = precision_counts.get(precision, 0) + 1

            logger.info(f"[ENRICH] Precision breakdown: {precision_counts}")

            if len(activities_with_coords) > 0:
                # Show first 3 examples
                for i, act in enumerate(activities_with_coords[:3]):
                    coords = act["location"]["coordinates"]
                    precision = act.get("location", {}).get("coordinates_precision", "unknown")
                    logger.info(f"[ENRICH]   Example {i+1}: {act['id']} -> {coords} ({precision})")


        except Exception as e:
            logger.error(f"Error enriching activities with locations: {e}", exc_info=True)
            # Don't fail the search if enrichment fails
            pass

    async def _enrich_via_attraction_matching(self, activities: list[dict]):
        """
        LEVEL 2: Enrich activities using attraction coordinates (reverse lookup).

        Strategy:
        - For activities without coordinates, find matching attractions by productCode
        - Attractions have direct coordinates from Viator
        - Provides precise location for museum visits, monument tours, etc.

        Args:
            activities: List of activity dicts (will be modified in-place)
        """
        try:
            # Filter activities needing enrichment
            candidates = [
                a for a in activities
                if not a.get("location", {}).get("coordinates")
            ]

            if not candidates:
                logger.info("[LEVEL 2] No activities need attraction matching")
                return

            logger.info(f"[LEVEL 2] Attempting attraction matching for {len(candidates)} activities")

            # Collect unique destination IDs
            destination_ids = list(set([a.get("_destination_id") for a in candidates if a.get("_destination_id")]))

            if not destination_ids:
                logger.warning("[LEVEL 2] No destination IDs available for attraction matching")
                return

            # Bulk lookup: productCode → attraction
            # Note: We search by destination for performance (attractions are indexed by destination)
            enriched_count = 0

            for destination_id in destination_ids:
                # Get product codes for this destination
                dest_products = [
                    a["id"] for a in candidates
                    if a.get("_destination_id") == destination_id
                ]

                if not dest_products:
                    continue

                # Bulk reverse lookup
                attractions_map = await self.attractions_repo.find_by_product_codes_bulk(
                    dest_products,
                    destination_id
                )

                logger.info(
                    f"[LEVEL 2] Found {len(attractions_map)} attractions for {len(dest_products)} products "
                    f"in destination {destination_id}"
                )

                # Assign coordinates from attractions
                for activity in candidates:
                    if activity.get("_destination_id") != destination_id:
                        continue

                    if activity.get("location", {}).get("coordinates"):
                        continue  # Already enriched

                    product_code = activity["id"]
                    attraction = attractions_map.get(product_code)

                    if attraction and attraction.get("location", {}).get("coordinates"):
                        coords = attraction["location"]["coordinates"]
                        activity["location"]["coordinates"] = coords
                        activity["location"]["coordinates_precision"] = "attraction"
                        activity["location"]["coordinates_source"] = f"attraction_{attraction.get('attraction_id')}"

                        logger.info(
                            f"[LEVEL 2] Enriched {product_code} via attraction "
                            f"{attraction.get('attraction_id')}: {coords}"
                        )
                        enriched_count += 1

            logger.info(f"[LEVEL 2] Enriched {enriched_count}/{len(candidates)} activities via attractions")

        except Exception as e:
            logger.error(f"[LEVEL 2] Error during attraction matching: {e}", exc_info=True)
            # Don't fail - continue to next level

    async def _enrich_via_geocoding(self, activities: list[dict], language: str = "en"):
        """
        LEVEL 3: Geocoding intelligent with MAXIMUM cost optimization.

        Strategy (Cost Optimization Priority):
        1. CHECK CACHE FIRST - Avoid ALL external calls if possible
        2. Batch translate titles (1 API call instead of N)
        3. Geoapify FIRST (3000/day FREE quota)
        4. Google Places FALLBACK ONLY (quota-limited, expensive)
        5. Circuit breaker if quota exceeded
        6. Validate coordinates within city bounds

        Args:
            activities: List of activity dicts (will be modified in-place)
            language: Current language (for translation)
        """
        # Feature flag - can disable if costs too high
        if not self.enable_geocoding:
            logger.info("[LEVEL 3] Geocoding is DISABLED (feature flag)")
            return

        # Verify services are available
        if not self.geoapify_client and not self.google_places_client:
            logger.warning("[LEVEL 3] No geocoding clients available")
            return

        if not self.translation_client:
            logger.warning("[LEVEL 3] No translation client available")
            return

        try:
            # Filter activities needing geocoding
            candidates = [
                a for a in activities
                if not a.get("location", {}).get("coordinates")
            ]

            if not candidates:
                logger.info("[LEVEL 3] No activities need geocoding")
                return

            logger.info(f"[LEVEL 3] Starting cost-optimized geocoding for {len(candidates)} activities")

            # === STEP 1: BATCH TRANSLATION (Minimize API calls) ===
            logger.info(f"[LEVEL 3] Step 1: Batch translating {len(candidates)} titles...")

            # Collect all titles
            titles = [a.get("title", "") for a in candidates]

            # Batch translate to English (more API calls but necessary for accuracy)
            # Using asyncio.gather for parallel execution
            translation_tasks = [
                self.translation_client.translate_to_english(title)
                for title in titles
            ]
            titles_en = await asyncio.gather(*translation_tasks, return_exceptions=True)

            # Filter out exceptions
            titles_en = [
                t if not isinstance(t, Exception) else titles[i]
                for i, t in enumerate(titles_en)
            ]

            logger.info(f"[LEVEL 3] Batch translation completed")

            # === STEP 2: CACHE CHECK (Avoid external API calls) ===
            logger.info(f"[LEVEL 3] Step 2: Checking cache for all activities...")

            cache_hits = 0
            cache_misses = []

            for i, activity in enumerate(candidates):
                title_en = titles_en[i]
                destination = activity.get("location", {}).get("destination", "")

                # Check cache FIRST
                cached = await self.geocoding_cache_repo.get(title_en, destination)

                if cached and cached.get("coordinates"):
                    # CACHE HIT - No API call needed!
                    coords = cached["coordinates"]
                    activity["location"]["coordinates"] = coords
                    activity["location"]["coordinates_precision"] = "geocoded"
                    activity["location"]["coordinates_source"] = f"cache_{cached.get('source', 'unknown')}"

                    cache_hits += 1
                    logger.debug(f"[LEVEL 3] Cache HIT: {title_en[:50]} → {coords}")
                else:
                    # CACHE MISS - Need to geocode
                    cache_misses.append((activity, title_en, destination))

            logger.info(
                f"[LEVEL 3] Cache results: {cache_hits} hits, {len(cache_misses)} misses "
                f"({cache_hits / len(candidates) * 100:.1f}% hit rate)"
            )

            if not cache_misses:
                logger.info("[LEVEL 3] All activities resolved from cache - ZERO API calls!")
                return

            # === STEP 3: GEOCODE CACHE MISSES (Geoapify → Google fallback) ===
            logger.info(f"[LEVEL 3] Step 3: Geocoding {len(cache_misses)} cache misses...")

            enriched_count = 0
            geoapify_count = 0
            google_count = 0

            for activity, title_en, destination in cache_misses:
                destination_id = activity.get("_destination_id")

                # Try Geoapify FIRST (FREE 3000/day)
                coords = None
                source = None

                if self.geoapify_client:
                    try:
                        result = await self.geoapify_client.fetch_by_name(
                            name=title_en,
                            city=destination,
                            lang="en"
                        )

                        if result and result.get("location"):
                            coords = {
                                "lat": result["location"].get("lat"),
                                "lon": result["location"].get("lng") or result["location"].get("lon")
                            }

                            # Validate coordinates within city bounds
                            if await self._validate_coords_in_city(coords, destination_id):
                                source = "geoapify"
                                geoapify_count += 1
                                logger.info(f"[LEVEL 3] Geoapify SUCCESS: {title_en[:50]}")
                            else:
                                logger.warning(f"[LEVEL 3] Geoapify coords INVALID (outside city): {title_en[:50]}")
                                coords = None

                    except Exception as e:
                        logger.warning(f"[LEVEL 3] Geoapify error for {title_en[:50]}: {e}")

                # Fallback to Google Places if Geoapify failed
                if not coords and self.google_places_client:
                    try:
                        result = await self.google_places_client.text_search(
                            poi_name=title_en,
                            city=destination
                        )

                        if result and result.get("location"):
                            coords = {
                                "lat": result["location"].get("latitude"),
                                "lon": result["location"].get("longitude")
                            }

                            # Validate coordinates within city bounds
                            if await self._validate_coords_in_city(coords, destination_id):
                                source = "google_places"
                                google_count += 1
                                logger.info(f"[LEVEL 3] Google Places SUCCESS: {title_en[:50]}")
                            else:
                                logger.warning(f"[LEVEL 3] Google coords INVALID (outside city): {title_en[:50]}")
                                coords = None

                    except RuntimeError as e:
                        if "quota" in str(e).lower() or "cap" in str(e).lower():
                            logger.error("[LEVEL 3] Google Places QUOTA EXCEEDED - Stopping geocoding")
                            break  # CIRCUIT BREAKER
                        else:
                            logger.warning(f"[LEVEL 3] Google Places error for {title_en[:50]}: {e}")
                    except Exception as e:
                        logger.warning(f"[LEVEL 3] Google Places error for {title_en[:50]}: {e}")

                # If geocoding succeeded, assign and cache
                if coords and source:
                    activity["location"]["coordinates"] = coords
                    activity["location"]["coordinates_precision"] = "geocoded"
                    activity["location"]["coordinates_source"] = source

                    # Cache for future use
                    await self.geocoding_cache_repo.set(title_en, destination, coords, source)

                    enriched_count += 1

            logger.info(
                f"[LEVEL 3] Geocoding completed: {enriched_count}/{len(cache_misses)} enriched "
                f"(Geoapify: {geoapify_count}, Google: {google_count})"
            )

            # Final summary
            total_enriched = cache_hits + enriched_count
            logger.info(
                f"[LEVEL 3] TOTAL: {total_enriched}/{len(candidates)} activities geocoded "
                f"({cache_hits} from cache, {enriched_count} from API)"
            )

        except Exception as e:
            logger.error(f"[LEVEL 3] Error during geocoding: {e}", exc_info=True)
            # Don't fail - continue to next level

    async def _validate_coords_in_city(self, coords: dict, destination_id: str) -> bool:
        """
        Validate that geocoded coordinates are within city bounds.

        Prevents false matches from geocoding (e.g., "Paris" in Texas instead of France).

        Args:
            coords: {"lat": float, "lon": float}
            destination_id: Viator destination ID

        Returns:
            True if coordinates are valid, False otherwise
        """
        if not coords or not destination_id:
            return False

        try:
            # Get destination center
            dest_coords = await self.location_resolver.get_destination_coordinates(destination_id)
            if not dest_coords:
                logger.warning(f"[VALIDATION] No coordinates for destination {destination_id}")
                return True  # Can't validate, assume valid

            # Calculate distance from city center
            from app.utils.coordinate_dispersion import _haversine_distance

            distance_km = _haversine_distance(
                dest_coords["lat"], dest_coords["lon"],
                coords["lat"], coords["lon"]
            )

            # Max 50km from city center (configurable)
            MAX_DISTANCE_KM = 50.0

            if distance_km > MAX_DISTANCE_KM:
                logger.warning(
                    f"[VALIDATION] Coordinates too far from city center: "
                    f"{distance_km:.1f}km > {MAX_DISTANCE_KM}km"
                )
                return False

            logger.debug(f"[VALIDATION] Coordinates valid: {distance_km:.1f}km from center")
            return True

        except Exception as e:
            logger.error(f"[VALIDATION] Error validating coordinates: {e}")
            return True  # On error, assume valid to avoid blocking

    async def _enrich_via_dispersion(self, activities: list[dict]):
        """
        LEVEL 4: Intelligent deterministic dispersion for activities without coordinates.

        Strategy:
        - Use hash-based seeding for deterministic but varied distribution
        - Apply sqrt distribution for natural clustering near center
        - Looks random on map but is repeatable (same activity = same coords)

        Args:
            activities: List of activity dicts (will be modified in-place)
        """
        try:
            # Filter activities needing dispersion
            candidates = [
                a for a in activities
                if not a.get("location", {}).get("coordinates")
            ]

            if not candidates:
                logger.info("[LEVEL 4] No activities need dispersion")
                return

            logger.info(f"[LEVEL 4] Applying intelligent dispersion to {len(candidates)} activities")

            dispersed_count = 0

            for activity in candidates:
                destination_id = activity.get("_destination_id")
                if not destination_id:
                    logger.warning(f"[LEVEL 4] No destination_id for activity {activity['id']}")
                    continue

                # Get destination center coordinates
                dest_coords = await self.location_resolver.get_destination_coordinates(destination_id)
                if not dest_coords:
                    logger.warning(f"[LEVEL 4] No coordinates for destination {destination_id}")
                    continue

                # Get adaptive radius from destination (TODO: add to destinations collection)
                # For now, use default 5km
                city_radius_km = 5.0

                # Generate dispersed coordinates
                dispersed = generate_dispersed_coordinates(
                    activity_id=activity["id"],
                    destination_id=destination_id,
                    city_center=dest_coords,
                    city_radius_km=city_radius_km
                )

                # Assign to activity
                activity["location"]["coordinates"] = dispersed["coordinates"]
                activity["location"]["coordinates_precision"] = dispersed["precision"]
                activity["location"]["coordinates_source"] = dispersed["source"]
                activity["location"]["_dispersion_metadata"] = {
                    "offset_km": dispersed["offset_km"],
                    "angle_degrees": dispersed["angle_degrees"],
                    "city_radius_km": city_radius_km
                }

                logger.info(
                    f"[LEVEL 4] Dispersed {activity['id']}: "
                    f"{dispersed['offset_km']}km at {dispersed['angle_degrees']}° from center"
                )
                dispersed_count += 1

            logger.info(f"[LEVEL 4] Dispersed {dispersed_count}/{len(candidates)} activities")

        except Exception as e:
            logger.error(f"[LEVEL 4] Error during dispersion: {e}", exc_info=True)
            # Don't fail - activities without coords will be returned as-is

    async def _apply_geo_filtering(
        self,
        activities: list[dict],
        search_coords: dict,
        radius_km: float,
        original_total: int
    ) -> tuple[list[dict], int]:
        """
        Apply geographic filtering for coordinate-based searches.

        Strategy:
        - Calculate distance from search point for each activity
        - Filter activities outside the specified radius
        - Add distance_from_search field to each activity
        - Sort by distance (ascending)

        Args:
            activities: List of activity dicts
            search_coords: {"lat": float, "lon": float} - search center point
            radius_km: Maximum distance from search point
            original_total: Original total count before filtering

        Returns:
            Tuple of (filtered_activities, filtered_total)
        """
        try:
            from app.utils.coordinate_dispersion import _haversine_distance

            logger.info(
                f"[GEO] Filtering {len(activities)} activities within {radius_km}km "
                f"of ({search_coords['lat']:.4f}, {search_coords['lon']:.4f})"
            )

            # Calculate distance for each activity and filter
            filtered = []
            skipped_no_coords = 0

            for activity in activities:
                coords = activity.get("location", {}).get("coordinates")

                if not coords or not coords.get("lat") or not coords.get("lon"):
                    # Skip activities without coordinates
                    skipped_no_coords += 1
                    continue

                # Calculate distance from search point
                distance_km = _haversine_distance(
                    search_coords["lat"], search_coords["lon"],
                    coords["lat"], coords["lon"]
                )

                # Filter by radius
                if distance_km <= radius_km:
                    # Add distance field
                    activity["distance_from_search"] = round(distance_km, 2)
                    filtered.append(activity)

            logger.info(
                f"[GEO] Filtered: {len(filtered)}/{len(activities)} activities within radius "
                f"(skipped {skipped_no_coords} without coords)"
            )

            # Sort by distance (ascending - closest first)
            filtered.sort(key=lambda x: x.get("distance_from_search", float('inf')))

            logger.info(
                f"[GEO] Sorted by distance. "
                f"Closest: {filtered[0]['distance_from_search']:.2f}km, "
                f"Farthest: {filtered[-1]['distance_from_search']:.2f}km"
                if filtered else "[GEO] No activities found within radius"
            )

            # Update total count to reflect filtered results
            filtered_total = len(filtered)

            return filtered, filtered_total

        except Exception as e:
            logger.error(f"[GEO] Error during geo filtering: {e}", exc_info=True)
            # On error, return original list without filtering
            return activities, original_total

    async def _resolve_tag_names(self, activities: list[dict], language: str = "en"):
        """
        Resolve tag IDs to human-readable names from MongoDB.

        Args:
            activities: List of activity dicts (will be modified in-place)
            language: Language code for tag names
        """
        try:
            # Step 1: Collect all unique tag IDs from all activities
            all_tag_ids = set()
            for activity in activities:
                categories = activity.get("categories", [])
                for category in categories:
                    # Categories are now strings like "367660", parse them
                    try:
                        tag_id = int(category)
                        all_tag_ids.add(tag_id)
                    except ValueError:
                        # Skip if not a numeric tag ID (e.g., "attraction")
                        continue

            if not all_tag_ids:
                logger.info("No tag IDs to resolve")
                return

            logger.info(f"Resolving {len(all_tag_ids)} unique tag IDs from MongoDB")

            # Step 2: Bulk fetch tags from MongoDB
            tags_map = await self.tags_repo.get_tags_bulk(list(all_tag_ids))

            logger.info(f"Found {len(tags_map)} tags in MongoDB")

            # Step 3: Replace tag IDs with names in each activity
            for activity in activities:
                categories = activity.get("categories", [])
                resolved_categories = []

                for category in categories:
                    try:
                        tag_id = int(category)
                        tag_doc = tags_map.get(tag_id)

                        if tag_doc:
                            # Get name in requested language, fallback to tag_name
                            tag_name = tag_doc.get("all_names", {}).get(language) or tag_doc.get("tag_name", f"tag_{tag_id}")
                            resolved_categories.append(tag_name)
                        else:
                            # Tag not found in DB, keep as generic
                            logger.debug(f"Tag {tag_id} not found in MongoDB")
                            resolved_categories.append(f"tag_{tag_id}")

                    except ValueError:
                        # Not a numeric tag ID (e.g., "attraction"), keep as-is
                        resolved_categories.append(category)

                # Replace categories with resolved names
                activity["categories"] = resolved_categories

            logger.info(f"Tag resolution completed for {len(activities)} activities")

        except Exception as e:
            logger.error(f"Error resolving tag names: {e}", exc_info=True)
            # Don't fail the search if tag resolution fails
            pass

    def _build_cache_key(self, destination_id: str, request: ActivitySearchRequest) -> str:
        """Build unique cache key for search request."""
        filters_dict = request.filters.model_dump() if request.filters else {}
        filters_str = json.dumps(filters_dict, sort_keys=True)
        filters_hash = hashlib.md5(filters_str.encode()).hexdigest()[:8]

        end_date = request.dates.end.isoformat() if request.dates.end else "none"

        # Include search_mode to differentiate activities/attractions/both
        mode = request.search_mode.value

        # Include geo info to differentiate city vs geo searches
        geo_suffix = ""
        if request.location.geo:
            geo_suffix = f":geo:{request.location.geo.lat:.4f}:{request.location.geo.lon:.4f}:{request.location.geo.radius_km}"

        return f"{destination_id}:{request.dates.start.isoformat()}:{end_date}:{filters_hash}:{mode}{geo_suffix}"

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
