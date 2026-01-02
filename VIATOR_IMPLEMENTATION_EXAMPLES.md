# Exemples de Code - Implémentation Viator API Wrapper

## 📦 Configuration & Setup

### 1. Mise à jour `.env`

```bash
# API Viator
VIATOR_API_KEY_DEV=1029cf59-4682-496d-8c16-9a229a388861
VIATOR_API_KEY_PROD=a8f758b5-0349-4eb0-99f6-41381526417c
VIATOR_ENV=dev  # dev ou prod
VIATOR_BASE_URL=https://api.viator.com

# Existing configs...
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_upstash_redis_token
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=poi_db
```

### 2. Mise à jour `requirements.txt`

```txt
# Existing
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
pydantic-settings==2.3.4
httpx==0.27.2
motor==3.6.0
pymongo==4.9.2
psycopg2-binary==2.9.9
rapidfuzz==3.6.1
upstash-redis==1.5.0

# Nouvelles dépendances
tenacity==8.2.3  # Pour retry logic
```

### 3. Configuration (`app/core/config.py`)

```python
from functools import lru_cache
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")

    app_name: str = "Travliaq API"

    # MongoDB
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongodb_db: str = Field(..., alias="MONGODB_DB")
    mongodb_collection_poi: str = Field("poi_details", alias="MONGODB_COLLECTION_POI")
    mongodb_collection_activities: str = Field("activities", alias="MONGODB_COLLECTION_ACTIVITIES")
    mongodb_collection_destinations: str = Field("destinations", alias="MONGODB_COLLECTION_DESTINATIONS")
    mongodb_collection_categories: str = Field("categories", alias="MONGODB_COLLECTION_CATEGORIES")

    # PostgreSQL/Supabase (optional)
    pg_host: str | None = Field(None, alias="PG_HOST")
    pg_database: str = Field("postgres", alias="PG_DATABASE")
    pg_user: str | None = Field(None, alias="PG_USER")
    pg_password: str | None = Field(None, alias="PG_PASSWORD")
    pg_port: int = Field(5432, alias="PG_PORT")
    pg_sslmode: str = Field("require", alias="PG_SSLMODE")

    # External APIs
    google_maps_api_key: str = Field(..., alias="GOOGLE_MAPS_API_KEY")
    geoapify_api_key: str = Field(..., alias="GEOAPIFY_API_KEY")
    google_flight_api_key: str = Field(..., alias="GOOGLE_FLIGHT_API")
    translation_service_url: str = Field("https://travliaq-transalte-production.up.railway.app", alias="TRANSLATION_SERVICE_URL")

    # Viator API (NEW)
    viator_api_key_dev: str = Field(..., alias="VIATOR_API_KEY_DEV")
    viator_api_key_prod: str = Field(..., alias="VIATOR_API_KEY_PROD")
    viator_env: str = Field("dev", alias="VIATOR_ENV")
    viator_base_url: str = Field("https://api.viator.com", alias="VIATOR_BASE_URL")

    @property
    def viator_api_key(self) -> str:
        """Get Viator API key based on environment."""
        return self.viator_api_key_prod if self.viator_env == "prod" else self.viator_api_key_dev

    # Upstash Redis
    upstash_redis_rest_url: str = Field(..., alias="UPSTASH_REDIS_REST_URL")
    upstash_redis_rest_token: str = Field(..., alias="UPSTASH_REDIS_REST_TOKEN")

    # Settings
    ttl_days: int = Field(365, description="Days before a POI document is considered stale")
    google_places_daily_cap: int = Field(9500, description="Soft cap to avoid exceeding free Google quotas")
    wikidata_user_agent: str = Field("poi-details-api/1.0", description="User agent used for Wikidata requests")
    default_detail_types: list[str] = Field(default_factory=lambda: ["hours", "pricing", "contact", "facts"])

    # Cache TTLs (NEW)
    cache_ttl_activities_search: int = Field(604800, description="7 days in seconds")
    cache_ttl_activity_details: int = Field(604800, description="7 days")
    cache_ttl_availability: int = Field(3600, description="1 hour")
    cache_ttl_destinations: int = Field(2592000, description="30 days")
    cache_ttl_categories: int = Field(2592000, description="30 days")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## 🔌 Client Viator API

### `app/services/viator/client.py`

```python
"""Viator API HTTP client with retry logic and rate limiting."""

from __future__ import annotations
import asyncio
import logging
from typing import Optional, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class ViatorAPIError(Exception):
    """Exception raised for Viator API errors."""
    pass


class ViatorRateLimitError(ViatorAPIError):
    """Exception raised when rate limit is exceeded."""
    pass


class ViatorClient:
    """HTTP client for Viator API with automatic retry and error handling."""

    def __init__(self, api_key: str, base_url: str = "https://api.viator.com", http_client: Optional[httpx.AsyncClient] = None):
        """
        Initialize Viator API client.

        Args:
            api_key: Viator API key (exp-api-key)
            base_url: Base URL for Viator API
            http_client: Optional shared httpx.AsyncClient instance
        """
        self.api_key = api_key
        self.base_url = base_url
        self.http_client = http_client or httpx.AsyncClient(timeout=30.0)
        self._own_client = http_client is None

        logger.info(f"ViatorClient initialized with base_url={base_url}")

    async def close(self):
        """Close HTTP client if owned by this instance."""
        if self._own_client:
            await self.http_client.aclose()

    def _build_headers(self, language: str = "en") -> dict:
        """Build request headers for Viator API."""
        return {
            "Accept": "application/json;version=2.0",
            "Accept-Language": language,
            "exp-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, ViatorRateLimitError)),
        reraise=True
    )
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        language: str = "en"
    ) -> dict:
        """
        Make HTTP request to Viator API with automatic retry.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/products/search")
            params: Query parameters
            json_data: JSON request body
            language: Accept-Language header value

        Returns:
            JSON response as dict

        Raises:
            ViatorAPIError: If API returns an error
            ViatorRateLimitError: If rate limit is exceeded
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._build_headers(language)

        logger.info(f"Viator API request: {method} {endpoint}")

        try:
            response = await self.http_client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            )

            # Log rate limit headers
            if "RateLimit-Remaining" in response.headers:
                logger.info(
                    f"Rate limit: {response.headers['RateLimit-Remaining']}/{response.headers.get('RateLimit-Limit', 'unknown')} remaining"
                )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limit exceeded, retry after {retry_after}s")
                raise ViatorRateLimitError(f"Rate limit exceeded, retry after {retry_after}s")

            # Handle other errors
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = e.response.text

            logger.error(f"Viator API error {e.response.status_code}: {error_detail}")
            raise ViatorAPIError(f"Viator API error {e.response.status_code}: {error_detail}")

        except httpx.RequestError as e:
            logger.error(f"Request error to Viator API: {e}")
            raise

    async def get(self, endpoint: str, params: Optional[dict] = None, language: str = "en") -> dict:
        """Make GET request to Viator API."""
        return await self.request("GET", endpoint, params=params, language=language)

    async def post(self, endpoint: str, json_data: dict, language: str = "en") -> dict:
        """Make POST request to Viator API."""
        return await self.request("POST", endpoint, json_data=json_data, language=language)
```

### `app/services/viator/products.py`

```python
"""Viator products API methods."""

from __future__ import annotations
import logging
from typing import Optional
from .client import ViatorClient

logger = logging.getLogger(__name__)


class ViatorProductsService:
    """Service for Viator /products/* endpoints."""

    def __init__(self, client: ViatorClient):
        self.client = client

    async def search_products(
        self,
        destination_id: str,
        start_date: str,
        end_date: Optional[str] = None,
        tags: Optional[list[int]] = None,
        lowest_price: Optional[float] = None,
        highest_price: Optional[float] = None,
        rating_from: Optional[float] = None,
        flags: Optional[list[str]] = None,
        sort: str = "DEFAULT",
        order: str = "ASCENDING",
        start: int = 1,
        count: int = 20,
        currency: str = "EUR",
        language: str = "en"
    ) -> dict:
        """
        Search products using /products/search endpoint.

        Args:
            destination_id: Viator destination ID (required)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (optional)
            tags: List of tag IDs for filtering
            lowest_price: Minimum price
            highest_price: Maximum price
            rating_from: Minimum rating (0-5)
            flags: List of flags (FREE_CANCELLATION, LIKELY_TO_SELL_OUT, etc.)
            sort: Sort method (DEFAULT, PRICE, TRAVELER_RATING, etc.)
            order: Sort order (ASCENDING, DESCENDING)
            start: Pagination start position (1-based)
            count: Number of results to return (max 50)
            currency: Currency code (EUR, USD, etc.)
            language: Language code for translations

        Returns:
            API response with products list
        """
        # Build filtering object
        filtering = {"destination": destination_id}

        if start_date:
            filtering["startDate"] = start_date
        if end_date:
            filtering["endDate"] = end_date
        if tags:
            filtering["tags"] = tags
        if lowest_price is not None:
            filtering["lowestPrice"] = lowest_price
        if highest_price is not None:
            filtering["highestPrice"] = highest_price
        if rating_from is not None:
            filtering["rating"] = {"from": rating_from}
        if flags:
            filtering["flags"] = flags

        # Build request body
        request_body = {
            "filtering": filtering,
            "currency": currency
        }

        # Add sorting if not default
        if sort != "DEFAULT":
            request_body["sorting"] = {
                "sort": sort,
                "order": order
            }

        # Add pagination
        request_body["pagination"] = {
            "start": start,
            "count": min(count, 50)  # Max 50 per API spec
        }

        logger.info(f"Searching products for destination {destination_id}")

        response = await self.client.post("/products/search", request_body, language=language)

        logger.info(f"Found {response.get('totalCount', 0)} products")

        return response

    async def get_product_details(self, product_code: str, language: str = "en") -> dict:
        """
        Get full product details.

        Args:
            product_code: Viator product code
            language: Language for translations

        Returns:
            Full product details
        """
        logger.info(f"Fetching product details for {product_code}")

        return await self.client.get(f"/products/{product_code}", language=language)
```

---

## 🗺️ Service de Résolution de Localisation

### `app/services/location_resolver.py`

```python
"""Service for resolving city names and geo coordinates to Viator destination IDs."""

from __future__ import annotations
import logging
from typing import Optional, Tuple
from rapidfuzz import fuzz, process
from motor.motor_asyncio import AsyncIOMotorCollection

logger = logging.getLogger(__name__)


class LocationResolver:
    """Resolve city names and geo coordinates to Viator destination IDs."""

    def __init__(self, destinations_collection: AsyncIOMotorCollection):
        """
        Initialize location resolver.

        Args:
            destinations_collection: MongoDB collection for destinations
        """
        self.destinations = destinations_collection
        self._cache = {}  # Simple in-memory cache for popular cities

    async def resolve_city(
        self,
        city: str,
        country_code: Optional[str] = None
    ) -> Optional[Tuple[str, str, float]]:
        """
        Resolve city name to Viator destination ID using fuzzy matching.

        Args:
            city: City name to search for
            country_code: ISO country code for filtering (optional but recommended)

        Returns:
            Tuple of (destination_id, matched_city_name, match_score) or None
        """
        # Check cache
        cache_key = f"{city.lower()}:{country_code or 'all'}"
        if cache_key in self._cache:
            logger.info(f"Cache hit for city resolution: {cache_key}")
            return self._cache[cache_key]

        # Build query
        query = {"type": "city"}
        if country_code:
            query["country_code"] = country_code.upper()

        # Fetch all cities (limited to 1000 for performance)
        cursor = self.destinations.find(query).limit(1000)
        cities = await cursor.to_list(length=1000)

        if not cities:
            logger.warning(f"No cities found for query: {query}")
            return None

        # Fuzzy matching
        city_names = [c["name"] for c in cities]
        match = process.extractOne(
            city,
            city_names,
            scorer=fuzz.ratio,
            score_cutoff=80  # Minimum 80% match
        )

        if not match:
            logger.warning(f"No fuzzy match found for city '{city}'")
            return None

        matched_name, score, _ = match

        # Find destination ID
        matched_city = next(c for c in cities if c["name"] == matched_name)
        destination_id = matched_city["destination_id"]

        logger.info(f"Resolved '{city}' → '{matched_name}' (ID: {destination_id}, score: {score})")

        result = (destination_id, matched_name, score)
        self._cache[cache_key] = result

        return result

    async def resolve_geo(
        self,
        lat: float,
        lon: float,
        radius_km: float = 50
    ) -> Optional[Tuple[str, str, float]]:
        """
        Find nearest Viator destination using geospatial query.

        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in kilometers

        Returns:
            Tuple of (destination_id, city_name, distance_km) or None
        """
        # MongoDB geospatial query (requires 2dsphere index)
        query = {
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]  # [lon, lat] order for GeoJSON
                    },
                    "$maxDistance": radius_km * 1000  # Convert to meters
                }
            },
            "type": "city"
        }

        destination = await self.destinations.find_one(query)

        if not destination:
            logger.warning(f"No destination found within {radius_km}km of ({lat}, {lon})")
            return None

        # Calculate distance (approximation)
        from math import radians, cos, sin, asin, sqrt

        def haversine(lon1, lat1, lon2, lat2):
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))
            km = 6371 * c
            return km

        dest_coords = destination["location"]["coordinates"]
        distance_km = haversine(lon, lat, dest_coords[0], dest_coords[1])

        logger.info(
            f"Resolved geo ({lat}, {lon}) → '{destination['name']}' "
            f"(ID: {destination['destination_id']}, distance: {distance_km:.1f}km)"
        )

        return (destination["destination_id"], destination["name"], distance_km)
```

---

## 🎨 Mapping Viator → Format Simplifié

### `app/utils/viator_mapper.py`

```python
"""Mapper to transform Viator API responses to simplified format."""

from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ViatorMapper:
    """Transform Viator API responses to simplified format for frontend."""

    @staticmethod
    def map_product_summary(product: dict) -> dict:
        """
        Transform Viator ProductSummary to simplified Activity format.

        Args:
            product: ProductSummary from Viator API

        Returns:
            Simplified activity dict
        """
        # Extract images
        images = []
        if product.get("images"):
            for img in product["images"]:
                variants = {}
                if img.get("variants"):
                    for variant in img["variants"]:
                        height = variant.get("height", 0)
                        if height <= 200:
                            variants["small"] = variant["url"]
                        elif height <= 600:
                            variants["medium"] = variant["url"]
                        else:
                            variants["large"] = variant["url"]

                images.append({
                    "url": img["variants"][0]["url"] if img.get("variants") else "",
                    "is_cover": img.get("isCover", False),
                    "variants": variants
                })

        # Extract pricing
        pricing_info = product.get("pricing", {})
        pricing_summary = pricing_info.get("summary", {})

        pricing = {
            "from_price": pricing_summary.get("fromPrice", 0),
            "currency": pricing_info.get("currency", "EUR"),
            "original_price": pricing_summary.get("fromPriceBeforeDiscount"),
            "is_discounted": pricing_summary.get("fromPriceBeforeDiscount") is not None
        }

        # Extract rating
        reviews = product.get("reviews", {})
        rating = {
            "average": reviews.get("combinedAverageRating", 0),
            "count": reviews.get("totalReviews", 0)
        }

        # Extract duration
        duration_obj = product.get("duration", {})
        duration_minutes = duration_obj.get("fixedDurationInMinutes", 0)

        duration = {
            "minutes": duration_minutes,
            "formatted": ViatorMapper._format_duration(duration_minutes)
        }

        # Extract destination
        destinations = product.get("destinations", [])
        primary_dest = destinations[0] if destinations else {}

        location = {
            "destination": primary_dest.get("name", "Unknown"),
            "country": primary_dest.get("country", "Unknown")
        }

        # Extract categories (tags → simple category names)
        tags = product.get("tags", [])
        categories = ViatorMapper._map_tags_to_categories(tags)

        # Build simplified activity
        return {
            "id": product.get("productCode"),
            "title": product.get("title", ""),
            "description": product.get("description", ""),
            "images": images,
            "pricing": pricing,
            "rating": rating,
            "duration": duration,
            "categories": categories,
            "flags": product.get("flags", []),
            "booking_url": product.get("productUrl", ""),
            "confirmation_type": product.get("confirmationType", "UNKNOWN"),
            "location": location,
            "availability": "available"  # Default - would need /availability/check for real status
        }

    @staticmethod
    def _format_duration(minutes: int) -> str:
        """Format duration in minutes to human-readable string."""
        if minutes == 0:
            return "Flexible"

        hours = minutes // 60
        mins = minutes % 60

        if hours > 0 and mins > 0:
            return f"{hours}h {mins}min"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{mins}min"

    @staticmethod
    def _map_tags_to_categories(tags: list[int]) -> list[str]:
        """
        Map Viator tag IDs to simplified category names.

        This is a simplified mapping - in production, maintain this in database.
        """
        # Simplified tag mapping (add more as needed)
        TAG_MAPPING = {
            21972: "food",
            21973: "dining",
            21975: "museum",
            21976: "art",
            20757: "popular",  # LIKELY_TO_SELL_OUT
            # Add more mappings from /products/tags endpoint
        }

        categories = []
        for tag_id in tags:
            if tag_id in TAG_MAPPING:
                category = TAG_MAPPING[tag_id]
                if category not in categories:
                    categories.append(category)

        return categories if categories else ["general"]
```

---

## 🎯 Service Métier Principal

### `app/services/activities_service.py`

```python
"""Business logic service for activities."""

from __future__ import annotations
import hashlib
import json
import logging
from typing import Optional
from datetime import datetime

from app.services.viator.client import ViatorClient
from app.services.viator.products import ViatorProductsService
from app.services.redis_cache import RedisCache
from app.services.location_resolver import LocationResolver
from app.repositories.activities_repository import ActivitiesRepository
from app.utils.viator_mapper import ViatorMapper
from app.models.activities import ActivitySearchRequest, ActivitySearchResponse

logger = logging.getLogger(__name__)


class ActivitiesService:
    """Business logic for activities search and management."""

    def __init__(
        self,
        viator_client: ViatorClient,
        viator_products: ViatorProductsService,
        redis_cache: RedisCache,
        activities_repo: ActivitiesRepository,
        location_resolver: LocationResolver,
        cache_ttl: int = 604800  # 7 days
    ):
        self.viator_client = viator_client
        self.viator_products = viator_products
        self.cache = redis_cache
        self.repo = activities_repo
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
                results=cached["results"],
                cache_info={
                    "cached": True,
                    "cached_at": cached.get("cached_at"),
                    "expires_at": cached.get("expires_at")
                }
            )

        logger.info(f"Cache MISS for activities search")

        # 3. Call Viator API
        viator_response = await self._call_viator_search(destination_id, request)

        # 4. Transform response
        activities = [
            ViatorMapper.map_product_summary(product)
            for product in viator_response.get("products", [])
        ]

        # 5. Persist in MongoDB (async, non-blocking)
        await self._persist_activities(activities)

        # 6. Cache results
        results = {
            "total": viator_response.get("totalCount", 0),
            "page": request.pagination.page,
            "limit": request.pagination.limit,
            "activities": activities
        }

        cache_data = {
            "results": results,
            "cached_at": datetime.utcnow().isoformat(),
            "expires_at": datetime.utcnow().isoformat()  # Compute expiration
        }

        self.cache.set("activities_search", {"key": cache_key}, cache_data, ttl_seconds=self.cache_ttl)

        return ActivitySearchResponse(
            success=True,
            location=matched_location,
            filters_applied=self._build_filters_summary(request),
            results=results,
            cache_info={
                "cached": False,
                "cached_at": None,
                "expires_at": None
            }
        )

    async def _resolve_location(self, location: dict) -> tuple[Optional[str], dict]:
        """Resolve location input to Viator destination ID."""
        # Option 1: Direct destination_id
        if location.get("destination_id"):
            return location["destination_id"], {
                "matched_city": None,
                "destination_id": location["destination_id"],
                "coordinates": None
            }

        # Option 2: City name
        if location.get("city"):
            result = await self.location_resolver.resolve_city(
                location["city"],
                location.get("country_code")
            )
            if result:
                dest_id, matched_city, score = result
                return dest_id, {
                    "matched_city": matched_city,
                    "destination_id": dest_id,
                    "coordinates": None,
                    "match_score": score
                }

        # Option 3: Geo coordinates
        if location.get("geo"):
            geo = location["geo"]
            result = await self.location_resolver.resolve_geo(
                geo["lat"],
                geo["lon"],
                geo.get("radius_km", 50)
            )
            if result:
                dest_id, city_name, distance_km = result
                return dest_id, {
                    "matched_city": city_name,
                    "destination_id": dest_id,
                    "coordinates": {"lat": geo["lat"], "lon": geo["lon"]},
                    "distance_km": distance_km
                }

        return None, {}

    async def _call_viator_search(self, destination_id: str, request: ActivitySearchRequest) -> dict:
        """Call Viator products search API."""
        # Map simple categories to Viator tags
        tags = self._map_categories_to_tags(request.filters.categories if request.filters else [])

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
            sort_mapping = {
                "default": "DEFAULT",
                "rating": "TRAVELER_RATING",
                "price": "PRICE"
            }
            kwargs["sort"] = sort_mapping.get(request.sorting.sort_by, "DEFAULT")
            kwargs["order"] = "DESCENDING" if request.sorting.order == "desc" else "ASCENDING"

        # Add pagination
        start = (request.pagination.page - 1) * request.pagination.limit + 1
        kwargs["start"] = start
        kwargs["count"] = request.pagination.limit

        return await self.viator_products.search_products(**kwargs)

    def _map_categories_to_tags(self, categories: Optional[list[str]]) -> Optional[list[int]]:
        """Map simplified categories to Viator tag IDs."""
        if not categories:
            return None

        # Simplified mapping - in production, fetch from database
        CATEGORY_TO_TAGS = {
            "food": [21972, 21973],
            "museum": [21975],
            "art": [21976],
            # Add more mappings
        }

        tags = []
        for category in categories:
            if category in CATEGORY_TO_TAGS:
                tags.extend(CATEGORY_TO_TAGS[category])

        return list(set(tags)) if tags else None

    async def _persist_activities(self, activities: list[dict]):
        """Persist activities to MongoDB (upsert)."""
        for activity in activities:
            try:
                await self.repo.upsert_activity(activity["id"], activity)
            except Exception as e:
                logger.error(f"Error persisting activity {activity['id']}: {e}")

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
```

---

## 📁 Repository MongoDB

### `app/repositories/activities_repository.py`

```python
"""MongoDB repository for activities."""

from __future__ import annotations
import logging
from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection

logger = logging.getLogger(__name__)


class ActivitiesRepository:
    """Repository for activities collection in MongoDB."""

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def upsert_activity(self, product_code: str, activity_data: dict):
        """
        Upsert activity with last_updated tracking.

        Args:
            product_code: Viator product code (unique identifier)
            activity_data: Activity data to store
        """
        result = await self.collection.update_one(
            {"product_code": product_code},
            {
                "$set": {
                    **activity_data,
                    "metadata.last_updated": datetime.utcnow()
                },
                "$setOnInsert": {
                    "metadata.first_seen": datetime.utcnow(),
                    "metadata.fetch_count": 0
                },
                "$inc": {
                    "metadata.fetch_count": 1
                }
            },
            upsert=True
        )

        if result.upserted_id:
            logger.info(f"Inserted new activity: {product_code}")
        else:
            logger.info(f"Updated existing activity: {product_code}")

    async def get_activity(self, product_code: str) -> Optional[dict]:
        """Get activity by product code."""
        return await self.collection.find_one({"product_code": product_code})

    async def search_activities(
        self,
        destination_id: Optional[str] = None,
        categories: Optional[list[str]] = None,
        limit: int = 20
    ) -> list[dict]:
        """Search activities in MongoDB (fallback when Viator API fails)."""
        query = {}

        if destination_id:
            query["destination.id"] = destination_id

        if categories:
            query["categories"] = {"$in": categories}

        cursor = self.collection.find(query).limit(limit)
        return await cursor.to_list(length=limit)

    async def create_indexes(self):
        """Create MongoDB indexes for activities collection."""
        indexes = [
            ("product_code", {"unique": True}),
            ("destination.id", {}),
            ("categories", {}),
            ("pricing.from_price", {}),
            ("rating.average", {}),
            ("location", {"2dsphere": True}),
            ("metadata.last_updated", {})
        ]

        for field, options in indexes:
            if options.get("2dsphere"):
                await self.collection.create_index([(field, "2dsphere")])
            elif options.get("unique"):
                await self.collection.create_index(field, unique=True)
            else:
                await self.collection.create_index(field)

        logger.info("Activities indexes created successfully")
```

---

## 🚀 Mise à jour `main.py`

```python
# Ajout dans app/main.py

from app.services.viator.client import ViatorClient
from app.services.viator.products import ViatorProductsService
from app.services.activities_service import ActivitiesService
from app.services.location_resolver import LocationResolver
from app.repositories.activities_repository import ActivitiesRepository

@app.on_event("startup")
async def startup_event() -> None:
    # ... existing code ...

    # Initialize Viator client
    app.state.viator_client = ViatorClient(
        api_key=settings.viator_api_key,
        base_url=settings.viator_base_url,
        http_client=app.state.http_client
    )

    app.state.viator_products = ViatorProductsService(app.state.viator_client)

    # Initialize activities repository
    activities_collection = app.state.mongo_manager.db[settings.mongodb_collection_activities]
    app.state.activities_repo = ActivitiesRepository(activities_collection)
    await app.state.activities_repo.create_indexes()

    # Initialize location resolver
    destinations_collection = app.state.mongo_manager.db[settings.mongodb_collection_destinations]
    app.state.location_resolver = LocationResolver(destinations_collection)

    # Initialize activities service
    app.state.activities_service = ActivitiesService(
        viator_client=app.state.viator_client,
        viator_products=app.state.viator_products,
        redis_cache=app.state.redis_cache,
        activities_repo=app.state.activities_repo,
        location_resolver=app.state.location_resolver,
        cache_ttl=settings.cache_ttl_activities_search
    )

@app.on_event("shutdown")
async def shutdown_event() -> None:
    # ... existing code ...
    await app.state.viator_client.close()
```

---

Ce fichier fournit tous les exemples de code nécessaires pour démarrer l'implémentation ! 🚀
