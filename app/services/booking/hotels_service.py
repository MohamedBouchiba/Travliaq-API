"""Hotels service for Booking.com API integration."""

from __future__ import annotations
import asyncio
import logging
import hashlib
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple

from app.models.hotels import (
    HotelSearchRequest, HotelSearchResponse, HotelSearchResults, HotelResult,
    HotelDetailsQuery, HotelDetailsResponse, HotelDetails, AmenityDetail,
    HotelPolicies, RoomOption,
    MapPricesRequest, MapPricesResponse, CityPriceResult,
    HotelSortBy, PropertyType, HotelAmenity
)
from app.core.config import get_settings
from app.repositories.hotels_repository import HotelsRepository
from .client import BookingClient, BookingAPIError

logger = logging.getLogger(__name__)


# Mapping Booking.com property type codes to our types
PROPERTY_TYPE_CODES = {
    PropertyType.HOTEL: "204",
    PropertyType.APARTMENT: "201",
    PropertyType.HOSTEL: "203",
    PropertyType.BED_AND_BREAKFAST: "208",
    PropertyType.VILLA: "213",
    PropertyType.RESORT: "206",
    PropertyType.GUEST_HOUSE: "216"
}

# Mapping our sort options to Booking.com order_by
SORT_MAPPING = {
    HotelSortBy.PRICE_ASC: "price",
    HotelSortBy.PRICE_DESC: "price",  # Will need to reverse results
    HotelSortBy.RATING: "review_score",
    HotelSortBy.DISTANCE: "distance",
    HotelSortBy.POPULARITY: "popularity"
}

# Mapping Booking.com amenity names to our normalized codes
AMENITY_MAPPING = {
    "wifi": ["wifi", "free wifi", "internet", "wireless internet"],
    "parking": ["parking", "free parking", "private parking"],
    "breakfast": ["breakfast", "breakfast included", "buffet breakfast"],
    "pool": ["pool", "swimming pool", "indoor pool", "outdoor pool"],
    "gym": ["gym", "fitness", "fitness center", "fitness centre"],
    "spa": ["spa", "wellness", "sauna"],
    "restaurant": ["restaurant", "on-site restaurant"],
    "bar": ["bar", "bar/lounge"],
    "ac": ["air conditioning", "air-conditioned", "climate control"],
    "kitchen": ["kitchen", "kitchenette", "cooking facilities"]
}


class HotelsService:
    """Service for hotel search and details operations."""

    def __init__(
        self,
        client: BookingClient,
        redis_cache: Optional[Any] = None,
        hotels_repository: Optional[HotelsRepository] = None
    ):
        """
        Initialize Hotels service.

        Args:
            client: BookingClient instance
            redis_cache: Optional Redis cache instance
            hotels_repository: Optional MongoDB repository for persistent caching
        """
        self.client = client
        self.cache = redis_cache
        self.repo = hotels_repository
        self._destination_cache: Dict[str, Tuple[str, str]] = {}  # city -> (dest_id, dest_type)

        logger.info("HotelsService initialized" + (" with MongoDB" if hotels_repository else ""))

    # =========================================================================
    # CACHE HELPERS
    # =========================================================================

    def _generate_cache_key(self, prefix: str, params: dict) -> str:
        """Generate cache key from prefix and parameters."""
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:16]
        return f"{prefix}:{param_hash}"

    async def _get_cached(self, prefix: str, params: dict) -> Optional[dict]:
        """Get cached data if available."""
        if not self.cache:
            return None
        try:
            key = self._generate_cache_key(prefix, params)
            return self.cache.get(prefix, {"key": key})
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    async def _set_cached(self, prefix: str, params: dict, data: dict, ttl_seconds: int):
        """Set data in cache."""
        if not self.cache:
            return
        try:
            key = self._generate_cache_key(prefix, params)
            self.cache.set(prefix, {"key": key}, data, ttl_seconds=ttl_seconds)
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    # =========================================================================
    # DESTINATION RESOLUTION
    # =========================================================================

    async def _resolve_destination(
        self,
        city: str,
        country_code: str = "",
        locale: str = "en-gb"
    ) -> Tuple[str, str]:
        """
        Resolve city name to Booking.com destination ID.

        Uses 3-tier caching: memory -> MongoDB -> API

        Args:
            city: City name
            country_code: ISO country code (for MongoDB lookup)
            locale: Language locale

        Returns:
            Tuple of (dest_id, dest_type)

        Raises:
            BookingAPIError: If destination not found
        """
        cache_key = f"{city.lower()}_{country_code.upper() if country_code else locale}"

        # 1. Check memory cache first (fastest)
        if cache_key in self._destination_cache:
            return self._destination_cache[cache_key]

        # 2. Check MongoDB (persistent)
        if self.repo and country_code:
            mongo_result = await self.repo.get_destination(city, country_code)
            if mongo_result:
                dest_id, dest_type = mongo_result
                self._destination_cache[cache_key] = (dest_id, dest_type)
                logger.info(f"Destination from MongoDB: {city} -> {dest_id}")
                return dest_id, dest_type

        # 3. Query API (expensive)
        results = await self.client.search_destination(city, locale)

        if not results:
            raise BookingAPIError(f"No destination found for: {city}")

        # Find best match (prefer city type)
        best_match = None
        for dest in results:
            dest_type = dest.get("dest_type", "")
            if dest_type == "city":
                best_match = dest
                break
            if not best_match:
                best_match = dest

        if not best_match:
            raise BookingAPIError(f"No destination found for: {city}")

        dest_id = str(best_match.get("dest_id", ""))
        dest_type = best_match.get("dest_type", "city")

        # Cache in memory
        self._destination_cache[cache_key] = (dest_id, dest_type)

        # Save to MongoDB (permanent)
        if self.repo and country_code:
            try:
                await self.repo.save_destination(city, country_code, dest_id, dest_type)
            except Exception as e:
                logger.warning(f"Failed to save destination to MongoDB: {e}")

        logger.info(f"Resolved destination via API: {city} -> {dest_id} ({dest_type})")
        return dest_id, dest_type

    # =========================================================================
    # DATA MAPPING
    # =========================================================================

    def _normalize_amenities(self, raw_amenities: List[Any]) -> List[str]:
        """Normalize amenity names to our standard codes."""
        normalized = set()

        for amenity in raw_amenities:
            # Handle both string and dict formats
            amenity_name = amenity if isinstance(amenity, str) else amenity.get("name", "")
            amenity_lower = amenity_name.lower()

            for code, keywords in AMENITY_MAPPING.items():
                if any(kw in amenity_lower for kw in keywords):
                    normalized.add(code)
                    break

        return list(normalized)

    def _map_hotel_result(self, raw: dict, currency: str, num_nights: int) -> Optional[HotelResult]:
        """Map raw Booking.com hotel to our HotelResult model."""
        try:
            hotel_id = str(raw.get("hotel_id", raw.get("id", "")))
            if not hotel_id:
                return None

            # New API structure: data is nested in 'property' object
            prop = raw.get("property", {})

            # Extract price from new structure first, then fallback to old
            price_per_night = 0.0
            price_breakdown = prop.get("priceBreakdown", {})
            if price_breakdown:
                gross_price = price_breakdown.get("grossPrice", {})
                if isinstance(gross_price, dict):
                    price_per_night = float(gross_price.get("value", 0)) / max(num_nights, 1)
            else:
                # Fallback to old structure
                price_data = raw.get("price_breakdown", raw.get("composite_price_breakdown", {}))
                if isinstance(price_data, dict):
                    gross = price_data.get("gross_amount_per_night", price_data.get("gross_amount", {}))
                    if isinstance(gross, dict):
                        price_per_night = float(gross.get("value", 0))
                    elif isinstance(gross, (int, float)):
                        price_per_night = float(gross)
                elif "min_total_price" in raw:
                    price_per_night = float(raw.get("min_total_price", 0)) / max(num_nights, 1)

            # Extract rating (new: property.reviewScore, old: review_score)
            rating = prop.get("reviewScore") or raw.get("review_score", raw.get("rating", 0))
            if rating and isinstance(rating, str):
                try:
                    rating = float(rating)
                except ValueError:
                    rating = 0

            # Extract coordinates (new: property.latitude/longitude)
            lat = float(prop.get("latitude") or raw.get("latitude", raw.get("lat", 0)))
            lng = float(prop.get("longitude") or raw.get("longitude", raw.get("lng", raw.get("lon", 0))))

            # Extract image (new: property.photoUrls)
            image_url = ""
            photo_urls = prop.get("photoUrls", [])
            if photo_urls:
                image_url = photo_urls[0] if isinstance(photo_urls[0], str) else ""
            if not image_url:
                image_url = raw.get("max_photo_url", raw.get("main_photo_url", ""))
            if not image_url:
                photos = raw.get("photos", [])
                if photos:
                    image_url = photos[0].get("url_max", photos[0].get("url", ""))

            # Extract amenities
            raw_amenities = raw.get("hotel_facilities", raw.get("facilities", []))
            amenities = self._normalize_amenities(raw_amenities) if raw_amenities else []

            # Extract name (new: property.name, old: hotel_name)
            name = prop.get("name") or raw.get("hotel_name", raw.get("name", "Unknown"))

            # Extract review count (new: property.reviewCount)
            review_count = int(prop.get("reviewCount", 0) or raw.get("review_nr", raw.get("review_count", 0)))

            # Extract stars (new: property.propertyClass)
            stars = prop.get("propertyClass") or raw.get("class", raw.get("stars"))

            return HotelResult(
                id=f"htl_{hotel_id}",
                name=name,
                lat=lat,
                lng=lng,
                imageUrl=image_url or None,
                stars=stars,
                rating=rating if rating else None,
                reviewCount=review_count,
                pricePerNight=round(price_per_night, 2),
                totalPrice=round(price_per_night * num_nights, 2) if price_per_night else None,
                currency=currency,
                address=raw.get("address", raw.get("address_trans", "")),
                distanceFromCenter=raw.get("distance_to_cc", raw.get("distance")),
                amenities=amenities,
                bookingUrl=raw.get("url", raw.get("hotel_url"))
            )

        except Exception as e:
            logger.warning(f"Error mapping hotel: {e}")
            return None

    def _map_hotel_details(
        self,
        details: dict,
        photos: List[dict],
        facilities: List[dict],
        rooms: dict,
        currency: str,
        num_nights: int
    ) -> HotelDetails:
        """Map raw Booking.com data to HotelDetails model."""
        hotel_id = str(details.get("hotel_id", details.get("id", "")))

        # Map photos
        image_urls = []
        for photo in photos[:20]:  # Limit to 20 images
            url = photo.get("url_max", photo.get("url_original", photo.get("url", "")))
            if url:
                image_urls.append(url)

        # Map amenities
        amenity_details = []
        for facility in facilities:
            name = facility.get("facility_name", facility.get("name", ""))
            if name:
                normalized = self._normalize_amenities([name])
                code = normalized[0] if normalized else name.lower().replace(" ", "_")
                amenity_details.append(AmenityDetail(code=code, label=name))

        # Map rooms from 'block' field (new API structure)
        room_options = []
        block_data = rooms.get("block", [])
        rooms_dict = rooms.get("rooms", {})

        for block in block_data[:10]:  # Limit to 10 rooms
            block_id = str(block.get("block_id", block.get("room_id", "")))
            if not block_id:
                continue

            # Extract room price from product_price_breakdown
            price_per_night = 0.0
            price_breakdown = block.get("product_price_breakdown", {})
            if price_breakdown:
                gross = price_breakdown.get("gross_amount", {})
                if isinstance(gross, dict):
                    total_price = float(gross.get("value", 0))
                    price_per_night = total_price / max(num_nights, 1)
                elif isinstance(gross, (int, float)):
                    price_per_night = float(gross) / max(num_nights, 1)

            # Fallback to old price structure
            if not price_per_night:
                price_data = block.get("price_breakdown", {})
                if isinstance(price_data, dict):
                    gross = price_data.get("gross_amount", 0)
                    if isinstance(gross, dict):
                        price_per_night = float(gross.get("value", 0)) / max(num_nights, 1)
                    elif isinstance(gross, (int, float)):
                        price_per_night = float(gross) / max(num_nights, 1)

            # Get room info from rooms dict if available
            room_info = rooms_dict.get(str(block.get("room_id", "")), {})
            bed_configs = room_info.get("bed_configurations", block.get("bed_configurations", []))
            bed_type = None
            if bed_configs and isinstance(bed_configs, list) and len(bed_configs) > 0:
                bed_type = bed_configs[0].get("bed_type")

            room_options.append(RoomOption(
                id=f"room_{block_id}",
                name=block.get("room_name", block.get("name", "Room")),
                description=room_info.get("description", block.get("room_description")),
                maxOccupancy=int(block.get("max_occupancy", block.get("max_persons", 2))),
                bedType=bed_type,
                pricePerNight=round(price_per_night, 2),
                totalPrice=round(price_per_night * num_nights, 2),
                amenities=self._normalize_amenities(room_info.get("facilities", [])),
                cancellationFree=block.get("refundable", block.get("is_free_cancellable", False))
            ))

        # Extract policies
        policies = None
        checkin_info = details.get("checkin", {})
        checkout_info = details.get("checkout", {})
        if checkin_info or checkout_info:
            policies = HotelPolicies(
                checkIn=checkin_info.get("from") if isinstance(checkin_info, dict) else None,
                checkOut=checkout_info.get("until") if isinstance(checkout_info, dict) else None,
                cancellation=details.get("cancellation_policy")
            )

        # Extract highlights
        highlights = []
        if details.get("review_score", 0) >= 9:
            highlights.append("Excellentes notes")
        if details.get("class", 0) >= 4:
            highlights.append("Hôtel de standing")

        return HotelDetails(
            id=f"htl_{hotel_id}",
            name=details.get("hotel_name", details.get("name", "Unknown")),
            lat=float(details.get("latitude", 0)),
            lng=float(details.get("longitude", 0)),
            stars=details.get("class"),
            rating=details.get("review_score"),
            reviewCount=int(details.get("review_nr", 0)),
            address=details.get("address", ""),
            distanceFromCenter=details.get("distance_to_cc"),
            description=details.get("description", details.get("hotel_description", "")),
            images=image_urls,
            amenities=amenity_details,
            highlights=highlights,
            policies=policies,
            rooms=room_options,
            bookingUrl=details.get("url")
        )

    # =========================================================================
    # FILTERING AND SORTING HELPERS
    # =========================================================================

    def _apply_filters_and_sort(
        self,
        hotels: List[HotelResult],
        request: HotelSearchRequest
    ) -> List[HotelResult]:
        """Apply filters and sorting to hotel list in-memory."""
        filtered = hotels

        if request.filters:
            # Price filter
            if request.filters.priceMin is not None:
                filtered = [h for h in filtered if h.pricePerNight >= request.filters.priceMin]
            if request.filters.priceMax is not None:
                filtered = [h for h in filtered if h.pricePerNight <= request.filters.priceMax]

            # Rating filter
            if request.filters.minRating is not None:
                filtered = [h for h in filtered if h.rating and h.rating >= request.filters.minRating]

            # Stars filter
            if request.filters.minStars is not None:
                filtered = [h for h in filtered if h.stars and h.stars >= request.filters.minStars]

            # Amenities filter
            if request.filters.amenities:
                required = set(a.value for a in request.filters.amenities)
                filtered = [h for h in filtered if required.issubset(set(h.amenities))]

            # Property types filter
            if request.filters.types:
                # Note: We don't have property type in HotelResult, skip for now
                pass

        # Apply sorting
        if request.sort == HotelSortBy.PRICE_ASC:
            filtered.sort(key=lambda h: h.pricePerNight or float('inf'))
        elif request.sort == HotelSortBy.PRICE_DESC:
            filtered.sort(key=lambda h: h.pricePerNight or 0, reverse=True)
        elif request.sort == HotelSortBy.RATING:
            filtered.sort(key=lambda h: h.rating or 0, reverse=True)
        elif request.sort == HotelSortBy.DISTANCE:
            filtered.sort(key=lambda h: h.distanceFromCenter or float('inf'))
        # POPULARITY is default order from API

        return filtered

    def _build_filters_applied(self, request: HotelSearchRequest) -> dict:
        """Build filters_applied dict for response."""
        total_adults = sum(r.adults for r in request.rooms)
        filters_applied = {
            "city": request.city,
            "dates": f"{request.checkIn} - {request.checkOut}",
            "rooms": len(request.rooms),
            "adults": total_adults,
            "sort": request.sort.value
        }
        if request.filters:
            filters_applied["filters"] = request.filters.model_dump(exclude_none=True)
        return filters_applied

    # =========================================================================
    # PUBLIC API: SEARCH HOTELS
    # =========================================================================

    async def search_hotels(
        self,
        request: HotelSearchRequest,
        force_refresh: bool = False
    ) -> HotelSearchResponse:
        """
        Search for hotels.

        Strategy: Cache maximum results WITHOUT filters, then apply filters in-memory.
        This way, different filter combinations share the same cache entry.

        Args:
            request: Search request parameters
            force_refresh: Force bypass cache

        Returns:
            HotelSearchResponse with results
        """
        # Build cache key WITHOUT filters/sort/pagination (shared cache for same city+dates)
        cache_params = {
            "city": request.city,
            "country": request.countryCode,
            "checkin": str(request.checkIn),
            "checkout": str(request.checkOut),
            "adults": sum(r.adults for r in request.rooms),
            "rooms": len(request.rooms),
            "currency": request.currency
            # NO filters, sort, limit, offset - these are applied in-memory
        }

        # Check cache (contains ALL hotels without filters)
        if not force_refresh:
            cached = await self._get_cached("hotel_search", cache_params)
            if cached:
                logger.info(f"Hotel search cache hit for {request.city}")
                # Apply filters/sort/pagination in-memory on cached data
                all_hotels = [HotelResult(**h) for h in cached.get("all_hotels", [])]
                filtered_hotels = self._apply_filters_and_sort(all_hotels, request)

                total_filtered = len(filtered_hotels)
                paginated = filtered_hotels[request.offset:request.offset + request.limit]

                return HotelSearchResponse(
                    results=HotelSearchResults(
                        hotels=paginated,
                        total=total_filtered,
                        hasMore=request.offset + len(paginated) < total_filtered
                    ),
                    filters_applied=self._build_filters_applied(request),
                    cache_info={"cached": True, "cached_at": cached.get("cached_at")}
                )

        # Resolve destination
        locale = f"{request.locale}-gb" if len(request.locale) == 2 else request.locale
        dest_id, dest_type = await self._resolve_destination(
            request.city,
            country_code=request.countryCode,
            locale=locale
        )

        # Calculate totals
        total_adults = sum(r.adults for r in request.rooms)
        total_children = sum(len(r.childrenAges) for r in request.rooms)
        children_ages = ",".join(
            str(age) for room in request.rooms for age in room.childrenAges
        ) if total_children > 0 else None

        num_nights = (request.checkOut - request.checkIn).days

        # Fetch MAXIMUM results WITHOUT filters by fetching multiple pages in parallel
        # This allows same cache to serve multiple filter combinations
        MAX_PAGES = 3  # Fetch 3 pages in parallel (~20-25 hotels/page = ~60-75 total)
        MAX_CACHE_HOTELS = 200

        async def fetch_page(page: int) -> list:
            """Fetch a single page of hotel results."""
            try:
                response = await self.client.search_hotels(
                    dest_id=dest_id,
                    dest_type=dest_type,
                    checkin_date=str(request.checkIn),
                    checkout_date=str(request.checkOut),
                    adults_number=total_adults,
                    room_number=len(request.rooms),
                    children_number=total_children,
                    children_ages=children_ages,
                    filter_by_currency=request.currency,
                    locale=locale,
                    order_by="popularity",  # Always fetch by popularity, sort in-memory
                    page_number=page
                    # NO price filters - applied in-memory
                )
                hotels = response.get("hotels", response.get("result", []))
                return hotels if isinstance(hotels, list) else []
            except Exception as e:
                logger.warning(f"Failed to fetch page {page}: {e}")
                return []

        # Fetch multiple pages in parallel for maximum data
        page_results = await asyncio.gather(*[fetch_page(p) for p in range(1, MAX_PAGES + 1)])

        # Combine all pages and deduplicate by hotel_id
        seen_ids = set()
        raw_hotels = []
        for page_hotels in page_results:
            for hotel in page_hotels:
                hotel_id = hotel.get("hotel_id") or hotel.get("property", {}).get("id")
                if hotel_id and hotel_id not in seen_ids:
                    seen_ids.add(hotel_id)
                    raw_hotels.append(hotel)

        logger.info(f"Fetched {len(raw_hotels)} unique hotels from {MAX_PAGES} pages for {request.city}")

        all_hotels = []
        for raw in raw_hotels[:MAX_CACHE_HOTELS]:
            hotel = self._map_hotel_result(raw, request.currency, num_nights)
            if hotel:
                all_hotels.append(hotel)

        # Cache ALL hotels (without filters)
        settings = get_settings()
        cache_data = {
            "all_hotels": [h.model_dump() for h in all_hotels],
            "total_from_api": len(all_hotels),  # Total unique hotels fetched from all pages
            "cached_at": datetime.utcnow().isoformat()
        }
        await self._set_cached("hotel_search", cache_params, cache_data, ttl_seconds=settings.cache_ttl_hotel_search)

        # Apply filters/sort/pagination in-memory
        filtered_hotels = self._apply_filters_and_sort(all_hotels, request)
        total_filtered = len(filtered_hotels)
        paginated = filtered_hotels[request.offset:request.offset + request.limit]

        results = HotelSearchResults(
            hotels=paginated,
            total=total_filtered,
            hasMore=request.offset + len(paginated) < total_filtered
        )

        # Save ALL hotels to MongoDB (static data + price history)
        if self.repo and all_hotels:
            try:
                hotels_data = [h.model_dump() for h in all_hotels]
                await self.repo.save_hotels_batch(hotels_data, request.city, request.countryCode)

                # Also save price history for each hotel
                for hotel in all_hotels:
                    if hotel.pricePerNight and hotel.pricePerNight > 0:
                        await self.repo.save_price_history(
                            hotel.id,
                            hotel.pricePerNight,
                            hotel.currency
                        )
            except Exception as e:
                logger.warning(f"Failed to save hotels to MongoDB: {e}")

        return HotelSearchResponse(
            results=results,
            filters_applied=self._build_filters_applied(request),
            cache_info={"cached": False}
        )

    # =========================================================================
    # PUBLIC API: HOTEL DETAILS
    # =========================================================================

    async def get_hotel_details(
        self,
        hotel_id: str,
        query: HotelDetailsQuery,
        force_refresh: bool = False
    ) -> HotelDetailsResponse:
        """
        Get detailed information about a hotel.

        Args:
            hotel_id: Hotel ID (with or without htl_ prefix)
            query: Query parameters
            force_refresh: Force bypass cache

        Returns:
            HotelDetailsResponse with full details
        """
        # Normalize hotel_id
        raw_hotel_id = hotel_id.replace("htl_", "")

        # Parse rooms from string format: "2-0,2-8-5"
        total_adults = 0
        room_count = 0
        for room_str in query.rooms.split(","):
            parts = room_str.split("-")
            if parts:
                total_adults += int(parts[0])
                room_count += 1

        num_nights = (query.checkOut - query.checkIn).days
        locale = f"{query.locale}-gb" if len(query.locale) == 2 else query.locale

        # Cache key
        cache_params = {
            "hotel_id": raw_hotel_id,
            "checkin": str(query.checkIn),
            "checkout": str(query.checkOut),
            "rooms": query.rooms,
            "currency": query.currency
        }

        # Check cache
        if not force_refresh:
            cached = await self._get_cached("hotel_details", cache_params)
            if cached:
                logger.info(f"Hotel details cache hit for {hotel_id}")
                return HotelDetailsResponse(
                    hotel=HotelDetails(**cached["hotel"]),
                    cache_info={"cached": True, "cached_at": cached.get("cached_at")}
                )

        # Fetch all data in parallel
        try:
            details, photos, facilities, rooms = await asyncio.gather(
                self.client.get_hotel_details(
                    hotel_id=raw_hotel_id,
                    checkin_date=str(query.checkIn),
                    checkout_date=str(query.checkOut),
                    adults_number=total_adults,
                    locale=locale,
                    currency_code=query.currency
                ),
                self.client.get_hotel_photos(raw_hotel_id, locale),
                self.client.get_hotel_facilities(raw_hotel_id, locale),
                self.client.get_hotel_rooms(
                    hotel_id=raw_hotel_id,
                    checkin_date=str(query.checkIn),
                    checkout_date=str(query.checkOut),
                    adults_number=total_adults,
                    room_number=room_count,
                    currency_code=query.currency,
                    locale=locale
                ),
                return_exceptions=True
            )

            # Handle partial failures
            if isinstance(details, Exception):
                raise details
            if isinstance(photos, Exception):
                photos = []
            if isinstance(facilities, Exception):
                facilities = []
            if isinstance(rooms, Exception):
                rooms = {}

        except BookingAPIError as e:
            logger.error(f"Failed to fetch hotel details: {e}")
            return HotelDetailsResponse(success=False, hotel=None)

        # Map to our model
        hotel = self._map_hotel_details(details, photos, facilities, rooms, query.currency, num_nights)

        # Cache results
        settings = get_settings()
        cache_data = {
            "hotel": hotel.model_dump(),
            "cached_at": datetime.utcnow().isoformat()
        }
        await self._set_cached("hotel_details", cache_params, cache_data, ttl_seconds=settings.cache_ttl_hotel_details)

        return HotelDetailsResponse(
            hotel=hotel,
            cache_info={"cached": False}
        )

    # =========================================================================
    # PUBLIC API: MAP PRICES
    # =========================================================================

    async def get_map_prices(
        self,
        request: MapPricesRequest,
        force_refresh: bool = False
    ) -> MapPricesResponse:
        """
        Get minimum prices for multiple cities.

        NOTE: This is expensive - 1 API call per city.
        Uses aggressive caching and limits concurrent calls.

        Args:
            request: Map prices request
            force_refresh: Force bypass cache

        Returns:
            MapPricesResponse with prices per city
        """
        # Limit to 5 cities max to reduce API costs
        cities = request.cities[:5]

        total_adults = sum(r.adults for r in request.rooms)
        total_children = sum(len(r.childrenAges) for r in request.rooms)
        children_ages = ",".join(
            str(age) for room in request.rooms for age in room.childrenAges
        ) if total_children > 0 else None

        prices: Dict[str, Optional[CityPriceResult]] = {}
        cities_to_fetch = []

        # Check cache for each city (Redis -> MongoDB -> API)
        for city in cities:
            city_key = f"{city.city}_{city.countryCode}"
            cache_params = {
                "city": city.city,
                "country": city.countryCode,
                "checkin": str(request.checkIn),
                "checkout": str(request.checkOut),
                "adults": total_adults
            }

            if not force_refresh:
                # 1. Check Redis cache first
                cached = await self._get_cached("hotel_map_price", cache_params)
                if cached:
                    prices[city_key] = CityPriceResult(**cached["price"]) if cached.get("price") else None
                    continue

                # 2. Check MongoDB for indicative price (no API call needed!)
                if self.repo:
                    mongo_price = await self.repo.get_city_indicative_price(
                        city.city,
                        city.countryCode
                    )
                    if mongo_price:
                        min_price, currency = mongo_price
                        prices[city_key] = CityPriceResult(
                            minPrice=round(min_price, 2),
                            currency=currency
                        )
                        logger.info(f"Map price from MongoDB: {city.city} -> {min_price} {currency}")
                        continue

            cities_to_fetch.append((city, city_key, cache_params))

        # Fetch missing cities with limited concurrency (reduced for cost optimization)
        if cities_to_fetch:
            semaphore = asyncio.Semaphore(2)  # Max 2 concurrent requests

            async def fetch_city_price(city_data):
                city, city_key, cache_params = city_data
                async with semaphore:
                    try:
                        # Resolve destination (with country_code for MongoDB caching)
                        dest_id, dest_type = await self._resolve_destination(
                            city.city,
                            country_code=city.countryCode
                        )

                        # Search with minimal results
                        response = await self.client.search_hotels(
                            dest_id=dest_id,
                            dest_type=dest_type,
                            checkin_date=str(request.checkIn),
                            checkout_date=str(request.checkOut),
                            adults_number=total_adults,
                            room_number=len(request.rooms),
                            children_number=total_children,
                            children_ages=children_ages,
                            filter_by_currency=request.currency,
                            order_by="price",  # Get cheapest first
                            page_number=0
                        )

                        # Extract min price
                        hotels = response.get("hotels", response.get("result", []))
                        min_price = None
                        nights = (request.checkOut - request.checkIn).days

                        for hotel in hotels[:5]:  # Check first 5
                            price = None

                            # New structure: property.priceBreakdown.grossPrice
                            prop = hotel.get("property", {})
                            price_breakdown = prop.get("priceBreakdown", {})
                            if price_breakdown:
                                gross_price = price_breakdown.get("grossPrice", {})
                                if isinstance(gross_price, dict) and gross_price.get("value"):
                                    price = float(gross_price.get("value", 0)) / max(nights, 1)

                            # Fallback to old structure
                            if not price:
                                price_data = hotel.get("price_breakdown", hotel.get("composite_price_breakdown", {}))
                                if isinstance(price_data, dict):
                                    gross = price_data.get("gross_amount_per_night", price_data.get("gross_amount", {}))
                                    if isinstance(gross, dict):
                                        price = float(gross.get("value", 0))
                                    elif isinstance(gross, (int, float)):
                                        price = float(gross)

                            if not price and "min_total_price" in hotel:
                                price = float(hotel.get("min_total_price", 0)) / max(nights, 1)

                            if price and price > 0 and (min_price is None or price < min_price):
                                min_price = price

                        result = CityPriceResult(
                            minPrice=round(min_price, 2) if min_price else None,
                            currency=request.currency
                        ) if min_price else None

                        # Cache result
                        settings = get_settings()
                        cache_data = {
                            "price": result.model_dump() if result else None,
                            "cached_at": datetime.utcnow().isoformat()
                        }
                        await self._set_cached("hotel_map_price", cache_params, cache_data, ttl_seconds=settings.cache_ttl_hotel_map_prices)

                        return city_key, result

                    except Exception as e:
                        logger.warning(f"Failed to fetch price for {city.city}: {e}")
                        return city_key, None

            # Fetch all cities
            results = await asyncio.gather(*[fetch_city_price(cd) for cd in cities_to_fetch])

            for city_key, result in results:
                prices[city_key] = result

        return MapPricesResponse(
            prices=prices,
            cache_info={"cached": len(cities_to_fetch) == 0}
        )
