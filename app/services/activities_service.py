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
            # UNIFIED SEARCH V2: Fetch activities and attractions separately
            logger.info(f"[UNIFIED_V2] Fetching BOTH activities AND attractions for destination {destination_id}")
            activities, attractions, total_activities, total_attractions = await self._search_unified(
                destination_id,
                request,
                user_preferences=request.user_preferences
            )

            # For backward compatibility, also set total_count (deprecated)
            total_count = total_activities + total_attractions

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

            # V2: Initialize separate pools (attractions mode → all go to attractions)
            attractions = activities
            activities = []
            total_attractions = total_count
            total_activities = 0

            logger.info(f"Transformed {len(attractions)} attractions from Viator response")

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

            # V2: Initialize separate pools (activities mode → all go to activities)
            attractions = []
            total_activities = total_count
            total_attractions = 0

            logger.info(f"Transformed {len(activities)} activities from Viator response")

            # REMOVED: Location enrichment (activities now display in list only)
            # Activities don't need coordinate enrichment - they are shown in list only
            # Attractions have precise coordinates from Viator

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

        # 6. Build results with V2 structure
        # V1 fields (backward compatibility - deprecated)
        combined_for_v1 = activities + attractions  # For clients using old 'activities' field

        results = SearchResults(
            # V1 fields (deprecated but kept for backward compatibility)
            total=total_count,
            page=request.pagination.page,
            limit=request.pagination.limit,
            activities=combined_for_v1,

            # V2 fields (NEW - separate activities and attractions)
            attractions=attractions,
            activities_list=activities,
            total_attractions=total_attractions,
            total_activities=total_activities,
            has_more=(total_activities + total_attractions) > (request.pagination.page * request.pagination.limit)
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

        # Option 3: Geo coordinates (point OR bounds)
        if location.geo:
            geo = location.geo

            # Check if bounds provided (map viewport search)
            if geo.bounds:
                logger.info(f"[GEO_BOUNDS] Converting bounds to center + radius...")
                center_lat, center_lon, radius_km = self._bounds_to_center_radius(geo.bounds.model_dump())

                result = await self.location_resolver.resolve_geo(
                    center_lat,
                    center_lon,
                    radius_km
                )
                if result:
                    dest_id, city_name, distance_km = result
                    return dest_id, LocationResolution(
                        matched_city=city_name,
                        destination_id=dest_id,
                        coordinates={"lat": center_lat, "lon": center_lon},
                        distance_km=distance_km,
                        search_type="geo_bounds"
                    )

            # Point search (existing)
            elif geo.lat is not None and geo.lon is not None:
                radius_km = geo.radius_km or 50  # Default radius
                result = await self.location_resolver.resolve_geo(
                    geo.lat,
                    geo.lon,
                    radius_km
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

    def _balance_results(
        self,
        merged_results: list[dict],
        target_count: int,
        target_ratio: Optional[dict[str, float]] = None
    ) -> list[dict]:
        """
        Balance merged results to achieve target type distribution.

        This function implements intelligent balancing to ensure a good mix of activities
        and attractions in the final results while respecting rating order as much as possible.

        Args:
            merged_results: Sorted list of activities and attractions (by rating, descending)
            target_count: Number of items to return (e.g., 50)
            target_ratio: Desired ratio {"activity": 0.5, "attraction": 0.5}
                         If None, uses equal 50/50 split

        Returns:
            Balanced subset of results

        Strategy:
        1. Walk through sorted list (by rating, descending)
        2. Select items while maintaining target ratio
        3. Prioritize higher-rated items
        4. If one type exhausted, fill remaining slots with other type
        """
        if target_ratio is None:
            target_ratio = {"activity": 0.5, "attraction": 0.5}

        # Target counts per type
        target_activities = int(target_count * target_ratio.get("activity", 0.5))
        target_attractions = int(target_count * target_ratio.get("attraction", 0.5))

        # Counters
        selected = []
        counts = {"activity": 0, "attraction": 0}

        # First pass: strict balancing while respecting rating order
        for item in merged_results:
            if len(selected) >= target_count:
                break

            item_type = item.get("type", "activity")

            # Check if we can add this type
            if item_type == "activity" and counts["activity"] < target_activities:
                selected.append(item)
                counts["activity"] += 1
            elif item_type == "attraction" and counts["attraction"] < target_attractions:
                selected.append(item)
                counts["attraction"] += 1

        # Second pass: fill remaining slots if one type exhausted
        # This ensures we still return target_count items even if one type has fewer results
        if len(selected) < target_count:
            for item in merged_results:
                if len(selected) >= target_count:
                    break

                if item not in selected:
                    selected.append(item)
                    item_type = item.get("type", "activity")
                    counts[item_type] = counts.get(item_type, 0) + 1

        logger.info(
            f"[BALANCE] Target: {target_count} items "
            f"({target_activities} activities/{target_attractions} attractions) "
            f"→ Result: {len(selected)} items "
            f"({counts['activity']} activities/{counts['attraction']} attractions)"
        )

        return selected[:target_count]

    def _score_and_rank_attractions(
        self,
        attractions: list[dict],
        limit: int = 15
    ) -> list[dict]:
        """
        Score and rank attractions by importance for map pin display.

        Importance formula: rating.average × rating.count
        This favors attractions that are both highly rated AND popular.

        Example:
        - Attraction A: 4.5★ × 500 reviews = 2250 (importance score)
        - Attraction B: 5.0★ × 10 reviews = 50 (importance score)
        → Attraction A is ranked higher despite lower rating

        Args:
            attractions: List of attraction dictionaries
            limit: Maximum number of attractions to return (default 15 for map pins)

        Returns:
            Top N attractions sorted by importance score (descending)
        """
        if not attractions:
            return []

        # Calculate importance score for each attraction
        for attraction in attractions:
            rating_data = attraction.get("rating", {})
            rating_avg = rating_data.get("average", 0)
            rating_count = rating_data.get("count", 0)

            # Importance = rating × popularity
            attraction["_importance_score"] = rating_avg * rating_count

        # Sort by importance score (descending)
        sorted_attractions = sorted(
            attractions,
            key=lambda x: x.get("_importance_score", 0),
            reverse=True
        )

        # Take top N
        top_attractions = sorted_attractions[:limit]

        logger.info(
            f"[ATTRACTION_SCORING] Scored {len(attractions)} attractions → "
            f"selected top {len(top_attractions)} for map pins"
        )

        if top_attractions:
            # Log top 3 for debugging
            for i, attr in enumerate(top_attractions[:3], 1):
                logger.debug(
                    f"  #{i}: {attr.get('title', 'Unknown')[:40]} - "
                    f"Score: {attr.get('_importance_score', 0):.0f} "
                    f"({attr.get('rating', {}).get('average', 0):.1f}★ × "
                    f"{attr.get('rating', {}).get('count', 0)} reviews)"
                )

        return top_attractions

    async def _search_unified(
        self,
        destination_id: str,
        request: ActivitySearchRequest,
        user_preferences: dict = None
    ) -> tuple[list[dict], list[dict], int, int]:
        """
        Unified search V2: Fetch activities and attractions SEPARATELY for distinct display.

        NEW Strategy (V2 - REFONTE UX):
        - Fetch activities (with filters) → Apply INTELLIGENT SCORING based on user preferences
        - Fetch ALL attractions available → Display ALL on map (no limit)
        - NO merging/balancing - they're displayed separately (list vs map)

        Args:
            destination_id: Viator destination ID
            request: Search request with filters and pagination
            user_preferences: User preferences for intelligent activity scoring (NEW)

        Returns:
            Tuple of (activities, attractions, total_activities, total_attractions)
            - activities: Top 40 scored by user preferences for LIST display
            - attractions: ALL attractions for MAP pins (no limit)
        """
        logger.info(f"[UNIFIED_V2] Starting separate fetch for destination {destination_id}")

        # V2: Different fetch strategies
        # Activities: Fetch more than limit for intelligent scoring (e.g., fetch 100 → score → top 40)
        activities_fetch_limit = max(request.pagination.limit * 2, 100)  # Over-fetch for better scoring
        activities_return_limit = request.pagination.limit  # e.g., 40

        # Attractions: Fetch ALL available (no limit)
        # Note: Viator API may have max per request, so fetch as many as possible
        attractions_limit = 500  # Fetch up to 500 attractions (Viator API max per request)

        logger.info(
            f"[UNIFIED_V2] Fetch strategy: {activities_fetch_limit} activities (for scoring → top {activities_return_limit}) + "
            f"{attractions_limit} attractions (ALL for map)"
        )

        # Prepare parallel tasks
        async def fetch_activities():
            """Fetch and transform activities, then apply intelligent scoring."""
            try:
                logger.info(f"[UNIFIED_V2] Fetching {activities_fetch_limit} activities for scoring...")

                # Over-fetch for better scoring results
                # Modify request pagination temporarily to fetch more
                original_limit = request.pagination.limit
                request.pagination.limit = activities_fetch_limit

                viator_response = await self._call_viator_search(destination_id, request)

                # Restore original limit
                request.pagination.limit = original_limit

                activities_raw = [
                    ViatorMapper.map_product_summary(product)
                    for product in viator_response.get("products", [])
                ]

                # Add type field
                for activity in activities_raw:
                    activity["type"] = "activity"

                logger.info(
                    f"[UNIFIED_V2] Fetched {len(activities_raw)} activities "
                    f"(total available: {viator_response.get('totalCount', 0)})"
                )

                # REMOVED: Coordinate enrichment not needed for activities (list-only display)

                # NEW: Apply intelligent scoring based on user preferences
                if user_preferences:
                    logger.info(f"[UNIFIED_V2] Applying intelligent scoring with user preferences...")
                    scored_activities = self._score_activities_by_preferences(
                        activities_raw,
                        user_preferences,
                        limit=activities_return_limit
                    )
                else:
                    # Fallback: sort by rating if no preferences
                    logger.info(f"[UNIFIED_V2] No preferences, sorting by rating (fallback)...")
                    sorted_activities = sorted(
                        activities_raw,
                        key=lambda x: x.get("rating", {}).get("average", 0),
                        reverse=True
                    )
                    scored_activities = sorted_activities[:activities_return_limit]

                logger.info(
                    f"[UNIFIED_V2] Scored and selected top {len(scored_activities)} activities "
                    f"from {len(activities_raw)} candidates"
                )

                return scored_activities, viator_response.get("totalCount", 0)
            except Exception as e:
                logger.error(f"[UNIFIED_V2] Error fetching activities: {e}")
                return [], 0

        async def fetch_attractions():
            """Fetch ALL attractions for map display (no scoring limit)."""
            try:
                logger.info(f"[UNIFIED_V2] Fetching ALL attractions (up to {attractions_limit})...")

                # Fetch ALL attractions (no filters - we want full coverage for map)
                viator_response = await self.viator_attractions.search_attractions(
                    destination_id=destination_id,
                    sort="DEFAULT",
                    start=1,
                    count=attractions_limit,
                    language=request.language
                )

                attractions_all = [
                    ViatorMapper.map_attraction(attraction)
                    for attraction in viator_response.get("attractions", [])
                ]

                # Add type field
                for attraction in attractions_all:
                    attraction["type"] = "attraction"

                logger.info(
                    f"[UNIFIED_V2] Fetched {len(attractions_all)} attractions "
                    f"(total available: {viator_response.get('totalCount', 0)})"
                )

                # NEW: Return ALL attractions (no limit to 15)
                # All attractions with precise Viator coordinates will be displayed on map
                return attractions_all, viator_response.get("totalCount", 0)
            except Exception as e:
                error_type = type(e).__name__
                logger.error(f"[UNIFIED_V2] Error fetching attractions ({error_type}): {e}")
                return [], 0

        # Execute both in parallel
        (activities, activities_total), (attractions, attractions_total) = await asyncio.gather(
            fetch_activities(),
            fetch_attractions()
        )

        logger.info(
            f"[UNIFIED_V2] Fetch complete: {len(activities)} activities + "
            f"{len(attractions)} attractions (separate pools)"
        )

        # V2: NO merging, NO balancing - they're displayed separately
        # Activities go to list panel, Attractions go to map pins

        return activities, attractions, activities_total, attractions_total

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

    # ========================================================================
    # ENRICHMENT SYSTEM REMOVED - 2026-01-03
    # ========================================================================
    #
    # Previously: 4-level hierarchical coordinate enrichment system (~597 lines)
    #
    # REMOVED METHODS:
    # 1. _enrich_activities_with_locations() - Main enrichment orchestrator
    # 2. _enrich_via_attraction_matching() - LEVEL 2: Reverse lookup via attractions
    # 3. _enrich_via_geocoding() - LEVEL 3: Geoapify + Google Places with cache
    # 4. _enrich_via_dispersion() - LEVEL 4: GeoGuessr-style deterministic spreading
    # 5. _validate_coords_in_city() - Coordinate validation helper
    #
    # RATIONALE:
    # - Activities now display in LIST ONLY (no map pins)
    # - Attractions have PRECISE coordinates directly from Viator
    # - Removes 600+ API calls per search (bulk products, bulk locations, geocoding)
    # - Improves API response time by 50-70%
    # - Simplifies codebase maintenance
    #
    # WHAT REMAINS:
    # - Activities: Returned as-is from Viator (no coordinate enrichment)
    # - Attractions: Have precise coordinates from Viator API
    # - Map: Displays ALL attractions (not activities)
    # - List: Displays activities sorted by intelligent scoring algorithm
    #
    # See: REFONTE_UX_COMPLETE.md for full context
    # ========================================================================

    def _score_activities_by_preferences(
        self,
        activities: list[dict],
        user_preferences: dict,
        limit: int = 40
    ) -> list[dict]:
        """
        Score and sort activities based on user preferences.

        Scoring Algorithm:
        - 40% Interest Matching: Categories match user interests (culture, food, nature, etc.)
        - 30% Price/Comfort Matching: Price aligns with user comfort level
        - 20% Pace Matching: Duration fits user pace (relaxed, moderate, intense)
        - 10% Rating Quality: Higher ratings score better

        Args:
            activities: List of activity dicts from Viator
            user_preferences: User preference dict with interests, comfortLevel, pace
            limit: Max number of activities to return (default: 40)

        Returns:
            Sorted list of activities (best matches first), limited to `limit`
        """
        if not activities:
            return []

        if not user_preferences:
            # Fallback: sort by rating if no preferences
            logger.info("[SCORING] No user preferences, sorting by rating")
            sorted_activities = sorted(
                activities,
                key=lambda x: x.get("rating", {}).get("average", 0),
                reverse=True
            )
            return sorted_activities[:limit]

        # Extract user preferences
        user_interests = user_preferences.get("interests", [])
        comfort_level = user_preferences.get("comfortLevel", 50)  # 0-100 scale
        pace = user_preferences.get("pace", "moderate")  # relaxed | moderate | intense

        logger.info(
            f"[SCORING] Scoring {len(activities)} activities with preferences: "
            f"interests={user_interests}, comfort={comfort_level}, pace={pace}"
        )

        # Score each activity
        for activity in activities:
            score = 0.0

            # === 1. INTEREST MATCHING (40% of score) ===
            activity_categories = [
                c.lower() for c in activity.get("categories", [])
            ]
            activity_tags = [
                t.lower() for t in activity.get("tags", [])
            ]
            activity_keywords = activity_categories + activity_tags

            # Count how many user interests match activity keywords
            interest_matches = 0
            for interest in user_interests:
                interest_lower = interest.lower()
                if any(interest_lower in keyword for keyword in activity_keywords):
                    interest_matches += 1

            if len(user_interests) > 0:
                interest_score = (interest_matches / len(user_interests)) * 40
            else:
                interest_score = 20  # Neutral score if no interests specified

            score += interest_score

            # === 2. PRICE/COMFORT MATCHING (30% of score) ===
            price = activity.get("pricing", {}).get("from_price", {}).get("amount", 0)

            # Price bands based on comfort level
            if comfort_level < 25:  # Budget (0-25)
                if price <= 30:
                    price_score = 30
                elif price <= 50:
                    price_score = 20
                else:
                    price_score = 5
            elif comfort_level < 50:  # Économique (25-50)
                if price <= 80:
                    price_score = 30
                elif price <= 120:
                    price_score = 20
                else:
                    price_score = 10
            elif comfort_level < 75:  # Confort (50-75)
                if price <= 150:
                    price_score = 30
                elif price <= 200:
                    price_score = 25
                else:
                    price_score = 15
            else:  # Luxe (75-100)
                if price >= 100:
                    price_score = 30
                elif price >= 60:
                    price_score = 25
                else:
                    price_score = 15

            score += price_score

            # === 3. PACE MATCHING (20% of score) ===
            duration_minutes = activity.get("duration", {}).get("fixed_duration_minutes", 0)

            # If no fixed duration, try to parse from formatted string
            if duration_minutes == 0:
                duration_str = activity.get("duration", {}).get("formatted", "")
                # Simple parsing for common formats (e.g., "3 hours", "2h30")
                if "hour" in duration_str.lower():
                    try:
                        hours = float(duration_str.split()[0])
                        duration_minutes = int(hours * 60)
                    except (ValueError, IndexError):
                        pass

            # Pace-based scoring
            if pace == "relaxed":
                # Relaxed: prefer shorter activities (1-3 hours)
                if 60 <= duration_minutes <= 180:
                    pace_score = 20
                elif duration_minutes < 60 or duration_minutes <= 240:
                    pace_score = 15
                else:
                    pace_score = 5
            elif pace == "moderate":
                # Moderate: prefer medium activities (2-5 hours)
                if 120 <= duration_minutes <= 300:
                    pace_score = 20
                elif 60 <= duration_minutes <= 360:
                    pace_score = 15
                else:
                    pace_score = 10
            else:  # intense
                # Intense: prefer longer activities (4+ hours)
                if duration_minutes >= 240:
                    pace_score = 20
                elif duration_minutes >= 180:
                    pace_score = 15
                else:
                    pace_score = 10

            score += pace_score

            # === 4. RATING QUALITY (10% of score) ===
            rating = activity.get("rating", {}).get("average", 0)
            rating_score = (rating / 5.0) * 10

            score += rating_score

            # Store score in activity for debugging/transparency
            activity["_preference_score"] = round(score, 2)

        # Sort by score (descending)
        sorted_activities = sorted(
            activities,
            key=lambda x: x.get("_preference_score", 0),
            reverse=True
        )

        # Log top 3 scores for debugging
        logger.info("[SCORING] Top 3 scored activities:")
        for i, activity in enumerate(sorted_activities[:3]):
            logger.info(
                f"  {i+1}. {activity.get('title', 'Unknown')[:50]} "
                f"(score: {activity.get('_preference_score', 0)})"
            )

        # Return top N activities
        return sorted_activities[:limit]

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

            # Check if radius_km is valid
            if radius_km is None or search_coords is None:
                logger.warning("[GEO] Skipping geo filtering: radius_km or search_coords is None")
                return activities, original_total

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

    def _bounds_to_center_radius(self, bounds: dict) -> tuple[float, float, float]:
        """
        Convert map viewport bounding box to center point + radius.

        Used for "search in this area" feature where user pans/zooms the map.

        Args:
            bounds: Dict with keys {north, south, east, west} (all floats)

        Returns:
            Tuple of (center_lat, center_lon, radius_km)

        Example:
            bounds = {"north": 48.9, "south": 48.8, "east": 2.4, "west": 2.3}
            → center: (48.85, 2.35), radius: ~7.8 km
        """
        from app.utils.coordinate_dispersion import _haversine_distance

        # Calculate center point
        center_lat = (bounds["north"] + bounds["south"]) / 2
        center_lon = (bounds["east"] + bounds["west"]) / 2

        # Calculate radius as distance from center to NE corner
        # This ensures the entire viewport is covered
        radius_km = _haversine_distance(
            center_lat, center_lon,
            bounds["north"], bounds["east"]
        )

        logger.debug(
            f"[BOUNDS_CONVERSION] Bounds → Center: ({center_lat:.4f}, {center_lon:.4f}), "
            f"Radius: {radius_km:.2f} km"
        )

        return center_lat, center_lon, radius_km

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
            # Bounds search (map viewport)
            if request.location.geo.bounds:
                bounds = request.location.geo.bounds
                geo_suffix = f":bounds:{bounds.north:.4f}:{bounds.south:.4f}:{bounds.east:.4f}:{bounds.west:.4f}"
            # Point search (lat/lon + radius)
            elif request.location.geo.lat is not None and request.location.geo.lon is not None:
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
