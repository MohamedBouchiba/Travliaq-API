"""Service for Google Flights API integration."""

from __future__ import annotations
import asyncio
import logging
from typing import Optional, TYPE_CHECKING
from datetime import date, datetime, timedelta
import httpx

from app.models.flights import (
    FlightSearchRequest,
    FlightSearchResponse,
    FlightItinerary,
    FlightSegment,
    Airport,
    Layover,
    Baggage,
    CarbonEmissions,
    FlightDuration,
    CalendarPricesRequest,
    CalendarPricesResponse,
    DailyPrice
)

if TYPE_CHECKING:
    from app.services.redis_cache import RedisCache
    from app.db.mongo import MongoManager

logger = logging.getLogger(__name__)


class FlightsService:
    """Service for searching flights using Google Flights API."""

    BASE_URL = "https://google-flights2.p.rapidapi.com/api/v1"
    CACHE_TTL = 86400  # 24 hours in seconds
    MAP_PRICES_CACHE_TTL = 172800  # 2 days in seconds
    MAP_PRICES_CONCURRENCY = 10  # Max concurrent API calls

    def __init__(
        self,
        api_key: str,
        redis_cache: "RedisCache",
        mongo_manager: "MongoManager" = None
    ):
        """
        Initialize the flights service.

        Args:
            api_key: RapidAPI key for Google Flights API
            redis_cache: Redis cache instance for caching results
            mongo_manager: MongoDB manager for persistent storage
        """
        self._api_key = api_key
        self._redis = redis_cache
        self._mongo = mongo_manager
        self._headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "google-flights2.p.rapidapi.com"
        }

    def search_flights(
        self,
        request: FlightSearchRequest
    ) -> Optional[FlightSearchResponse]:
        """
        Search for flights based on the given criteria.
        Results are cached in Redis for 24 hours.

        Args:
            request: Flight search parameters

        Returns:
            FlightSearchResponse with available flights
            None if API request fails

        Example:
            Search one-way flights from LAX to JFK:
            >>> request = FlightSearchRequest(
            ...     departure_id="LAX",
            ...     arrival_id="JFK",
            ...     outbound_date=date(2025, 4, 1),
            ...     adults=2
            ... )
            >>> response = service.search_flights(request)
        """
        try:
            # Build cache key parameters
            cache_params = {
                "departure_id": request.departure_id,
                "arrival_id": request.arrival_id,
                "outbound_date": request.outbound_date.isoformat(),
                "return_date": request.return_date.isoformat() if request.return_date else None,
                "adults": request.adults,
                "children": request.children,
                "infant_in_seat": request.infant_in_seat,
                "infant_on_lap": request.infant_on_lap,
                "travel_class": request.travel_class.value,
                "show_hidden": request.show_hidden,
                "currency": request.currency,
                "language_code": request.language_code,
                "country_code": request.country_code,
            }

            # Check cache first (v2 to avoid old format conflicts)
            cached = self._redis.get("flight_search_v2", cache_params)
            if cached:
                logger.info(f"Returning cached flights for {request.departure_id} → {request.arrival_id}")
                return FlightSearchResponse(**cached)

            # Build query parameters for API
            params = {
                "departure_id": request.departure_id,
                "arrival_id": request.arrival_id,
                "outbound_date": request.outbound_date.strftime("%Y-%m-%d"),
                "adults": str(request.adults),
                "children": str(request.children),
                "infant_in_seat": str(request.infant_in_seat),
                "infant_on_lap": str(request.infant_on_lap),
                "travel_class": request.travel_class.value,
                "show_hidden": "1" if request.show_hidden else "0",
                "currency": request.currency,
                "language_code": request.language_code,
                "country_code": request.country_code,
            }

            # Add return_date if round trip
            if request.return_date:
                params["return_date"] = request.return_date.strftime("%Y-%m-%d")

            logger.info(
                f"Searching flights: {request.departure_id} → {request.arrival_id} "
                f"on {request.outbound_date} (adults: {request.adults})"
            )

            # Make API request
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.BASE_URL}/searchFlights",
                    headers=self._headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()

            # Check API response status
            if not data.get("status"):
                logger.error(f"API returned error: {data.get('message')}")
                logger.error(f"Full API response: {data}")
                return None

            # Parse response
            api_data = data.get("data", {})
            logger.debug(f"API data structure: {list(api_data.keys())}")
            itineraries_data = api_data.get("itineraries", {})

            # Extract flights from different categories
            flights = []

            # Top flights (usually best value)
            top_flights = itineraries_data.get("topFlights", [])
            flights.extend(self._parse_itineraries(top_flights))

            # Other flights
            other_flights = itineraries_data.get("otherFlights", [])
            flights.extend(self._parse_itineraries(other_flights))

            # Get next_token if available
            next_token = api_data.get("next_token")

            logger.info(f"Found {len(flights)} flights for {request.departure_id} → {request.arrival_id}")

            response = FlightSearchResponse(
                itineraries=flights,
                next_token=next_token
            )

            # Cache the result for 24 hours
            self._redis.set(
                "flight_search_v2",
                cache_params,
                response.model_dump(mode='json'),
                ttl_seconds=self.CACHE_TTL
            )

            return response

        except httpx.HTTPError as e:
            logger.error(f"HTTP error searching flights: {e}", exc_info=True)
            return None

        except Exception as e:
            logger.error(f"Error searching flights: {e}", exc_info=True)
            return None

    def _parse_itineraries(self, raw_itineraries: list) -> list[FlightItinerary]:
        """
        Parse raw itineraries from API response.

        Args:
            raw_itineraries: List of raw itinerary data from API

        Returns:
            List of parsed FlightItinerary objects
        """
        itineraries = []

        for raw in raw_itineraries:
            try:
                # Parse flight segments
                flights = []
                raw_flights = raw.get("flights", [])
                for flight_data in raw_flights:
                    try:
                        # Parse departure airport
                        dep_data = flight_data.get("departure_airport", {})
                        dep_airport = Airport(
                            airport_name=dep_data.get("airport_name", ""),
                            airport_code=dep_data.get("airport_code", ""),
                            time=dep_data.get("time", "")
                        )

                        # Parse arrival airport
                        arr_data = flight_data.get("arrival_airport", {})
                        arr_airport = Airport(
                            airport_name=arr_data.get("airport_name", ""),
                            airport_code=arr_data.get("airport_code", ""),
                            time=arr_data.get("time", "")
                        )

                        # Parse duration
                        duration_data = flight_data.get("duration", {})
                        duration = FlightDuration(
                            raw=duration_data.get("raw", 0),
                            text=duration_data.get("text", "")
                        )

                        # Create flight segment
                        segment = FlightSegment(
                            departure_airport=dep_airport,
                            arrival_airport=arr_airport,
                            duration=duration,
                            airline=flight_data.get("airline", ""),
                            airline_logo=flight_data.get("airline_logo", ""),
                            flight_number=flight_data.get("flight_number", ""),
                            aircraft=flight_data.get("aircraft"),
                            seat=flight_data.get("seat"),
                            legroom=flight_data.get("legroom"),
                            extensions=flight_data.get("extensions"),
                            travel_class=flight_data.get("travel_class"),
                            overnight=flight_data.get("overnight")
                        )
                        flights.append(segment)
                    except Exception as e:
                        logger.warning(f"Failed to parse flight segment: {e}")
                        continue

                # Parse layovers
                layovers = None
                raw_layovers = raw.get("layovers")
                if raw_layovers:
                    layovers = []
                    for layover_data in raw_layovers:
                        try:
                            layover = Layover(
                                duration=layover_data.get("duration", 0),
                                airport_name=layover_data.get("airport_name", ""),
                                airport_code=layover_data.get("airport_code", ""),
                                duration_label=layover_data.get("duration_label"),
                                city=layover_data.get("city"),
                                overnight=layover_data.get("overnight")
                            )
                            layovers.append(layover)
                        except Exception as e:
                            logger.warning(f"Failed to parse layover: {e}")
                            continue

                # Parse baggage
                bags = None
                bags_data = raw.get("bags")
                if bags_data:
                    try:
                        bags = Baggage(
                            carry_on=bags_data.get("carry_on"),
                            checked=bags_data.get("checked")
                        )
                    except Exception as e:
                        logger.warning(f"Failed to parse baggage: {e}")

                # Parse carbon emissions
                carbon = None
                carbon_data = raw.get("carbon_emissions")
                if carbon_data:
                    try:
                        carbon = CarbonEmissions(
                            CO2e=carbon_data.get("CO2e", 0),
                            typical_for_this_route=carbon_data.get("typical_for_this_route", 0),
                            difference_percent=carbon_data.get("difference_percent", 0),
                            higher=carbon_data.get("higher")
                        )
                    except Exception as e:
                        logger.warning(f"Failed to parse carbon emissions: {e}")

                # Parse delay
                delay_value = None
                delay_data = raw.get("delay")
                if delay_data and isinstance(delay_data, dict):
                    delay_value = delay_data.get("text")
                elif isinstance(delay_data, (int, float)):
                    delay_value = delay_data

                # Create itinerary with all data
                itinerary = FlightItinerary(
                    flights=flights if flights else None,
                    layovers=layovers,
                    total_duration=raw.get("total_duration") or raw.get("duration", {}).get("raw"),
                    price=raw.get("price", 0.0),
                    booking_token=raw.get("booking_token"),
                    carbon_emissions=carbon,
                    bags=bags,
                    airline_logo=raw.get("airline_logo"),
                    delay=delay_value,
                    self_transfer=raw.get("self_transfer"),
                    # Legacy fields for backward compatibility
                    departure_time=raw.get("departure_time"),
                    arrival_time=raw.get("arrival_time"),
                    stops=raw.get("stops"),
                    airline=raw.get("airline")
                )

                itineraries.append(itinerary)

            except Exception as e:
                logger.warning(f"Failed to parse itinerary: {e}", exc_info=True)
                continue

        return itineraries

    def get_calendar_prices(
        self,
        request: CalendarPricesRequest
    ) -> Optional[CalendarPricesResponse]:
        """
        Get flight prices for a calendar range of dates.
        Results are cached in Redis for 24 hours.

        Args:
            request: Calendar price request parameters

        Returns:
            CalendarPricesResponse with daily prices
            None if API request fails

        Example:
            Get prices for LAX → JFK in April:
            >>> request = CalendarPricesRequest(
            ...     departure_id="LAX",
            ...     arrival_id="JFK",
            ...     outbound_date=date(2025, 4, 1),
            ...     start_date=date(2025, 4, 1),
            ...     end_date=date(2025, 4, 30)
            ... )
            >>> response = service.get_calendar_prices(request)
        """
        try:
            # Build cache key parameters
            cache_params = {
                "departure_id": request.departure_id,
                "arrival_id": request.arrival_id,
                "outbound_date": request.outbound_date.isoformat(),
                "start_date": request.start_date.isoformat() if request.start_date else None,
                "end_date": request.end_date.isoformat() if request.end_date else None,
                "adults": request.adults,
                "children": request.children,
                "infant_in_seat": request.infant_in_seat,
                "infant_on_lap": request.infant_on_lap,
                "trip_type": request.trip_type.value,
                "trip_days": request.trip_days,
                "travel_class": request.travel_class.value,
                "currency": request.currency,
                "country_code": request.country_code,
            }

            # Check cache first
            cached = self._redis.get("calendar_prices", cache_params)
            if cached:
                logger.info(f"Returning cached calendar prices for {request.departure_id} → {request.arrival_id}")
                return CalendarPricesResponse(**cached)

            # Build query parameters for API
            params = {
                "departure_id": request.departure_id,
                "arrival_id": request.arrival_id,
                "outbound_date": request.outbound_date.strftime("%Y-%m-%d"),
                "adults": str(request.adults),
                "children": str(request.children),
                "infant_in_seat": str(request.infant_in_seat),
                "infant_on_lap": str(request.infant_on_lap),
                "trip_type": request.trip_type.value,
                "trip_days": str(request.trip_days),
                "travel_class": request.travel_class.value,
                "currency": request.currency,
                "country_code": request.country_code,
            }

            # Add date range if specified
            if request.start_date:
                params["start_date"] = request.start_date.strftime("%Y-%m-%d")
            if request.end_date:
                params["end_date"] = request.end_date.strftime("%Y-%m-%d")

            logger.info(
                f"Getting calendar prices: {request.departure_id} → {request.arrival_id} "
                f"({request.start_date} to {request.end_date})"
            )

            # Make API request
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.BASE_URL}/getCalendarPicker",
                    headers=self._headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()

            # Check API response status
            if not data.get("status"):
                logger.error(f"API returned error: {data.get('message')}")
                return None

            # Parse response
            api_data = data.get("data", [])

            prices = []
            for item in api_data:
                try:
                    daily_price = DailyPrice(
                        departure=datetime.strptime(item["departure"], "%Y-%m-%d").date(),
                        price=item["price"],
                        return_date=datetime.strptime(item["return"], "%Y-%m-%d").date() if "return" in item else None
                    )
                    prices.append(daily_price)
                except Exception as e:
                    logger.warning(f"Failed to parse daily price: {e}")
                    continue

            logger.info(f"Found {len(prices)} daily prices")

            response = CalendarPricesResponse(
                prices=prices,
                currency=request.currency,
                trip_type=request.trip_type.value
            )

            # Cache the result for 24 hours
            self._redis.set(
                "calendar_prices",
                cache_params,
                response.model_dump(mode='json'),
                ttl_seconds=self.CACHE_TTL
            )

            return response

        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting calendar prices: {e}", exc_info=True)
            return None

        except Exception as e:
            logger.error(f"Error getting calendar prices: {e}", exc_info=True)
            return None

    async def get_map_prices(
        self,
        origin: str,
        destinations: list[str],
        adults: int = 1,
        currency: str = "EUR"
    ) -> tuple[dict[str, Optional[dict]], int, int]:
        """
        Get cheapest flight prices over next 3 months for multiple destinations.

        Optimized flow:
        1. Check cache for ALL destinations first (sync, fast)
        2. Only make API calls for uncached destinations (async, parallel)
        3. Merge results

        Args:
            origin: Origin IATA code
            destinations: List of destination IATA codes
            adults: Number of adult passengers
            currency: Currency code

        Returns:
            Tuple of (prices_dict, cached_count, fetched_count)
            prices_dict: {destination: {"price": float, "date": str} | None}
        """
        today = date.today()
        end_date = today + timedelta(days=90)

        results: dict[str, Optional[dict]] = {}
        to_fetch: list[str] = []

        # Phase 1: Check cache for all destinations (fast, synchronous)
        for destination in destinations:
            cache_params = self._build_map_price_cache_key(
                origin, destination, adults, currency, today, end_date
            )
            cached = self._redis.get("map_price", cache_params)

            if cached is not None:
                # Cache hit - add to results immediately
                results[destination] = cached.get("data")
                logger.debug(f"Cache HIT: {origin} -> {destination}")
            else:
                # Cache miss - need to fetch
                to_fetch.append(destination)

        cached_count = len(results)
        logger.info(
            f"Map prices cache check: {cached_count}/{len(destinations)} cached, "
            f"{len(to_fetch)} to fetch"
        )

        # Phase 2: Fetch only uncached destinations in parallel
        if to_fetch:
            semaphore = asyncio.Semaphore(self.MAP_PRICES_CONCURRENCY)

            async def fetch_and_cache(destination: str) -> tuple[str, Optional[dict]]:
                """Fetch price and cache result."""
                async with semaphore:
                    try:
                        result = await self._fetch_cheapest_price_async(
                            origin, destination, today, end_date, adults, currency
                        )

                        # Cache result (including None for no flights)
                        cache_params = self._build_map_price_cache_key(
                            origin, destination, adults, currency, today, end_date
                        )
                        self._redis.set(
                            "map_price",
                            cache_params,
                            {"data": result},
                            ttl_seconds=self.MAP_PRICES_CACHE_TTL
                        )

                        if result:
                            logger.info(
                                f"Fetched: {origin} -> {destination} = "
                                f"{result['price']} {currency} on {result['date']}"
                            )
                        else:
                            logger.info(f"Fetched: {origin} -> {destination} = No flights")

                        return (destination, result)

                    except Exception as e:
                        logger.error(f"Error {origin} -> {destination}: {e}")
                        return (destination, None)

            # Execute API calls in parallel
            tasks = [fetch_and_cache(dest) for dest in to_fetch]
            fetched_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Merge fetched results
            for result in fetched_results:
                if isinstance(result, Exception):
                    logger.error(f"Task exception: {result}")
                    continue
                dest, price_data = result
                results[dest] = price_data

        fetched_count = len(to_fetch)
        logger.info(
            f"Map prices complete: {len(results)} destinations "
            f"({cached_count} cached, {fetched_count} fetched)"
        )

        return results, cached_count, fetched_count

    def _build_map_price_cache_key(
        self,
        origin: str,
        destination: str,
        adults: int,
        currency: str,
        start_date: date,
        end_date: date
    ) -> dict:
        """Build cache key parameters for map price lookup."""
        return {
            "origin": origin,
            "destination": destination,
            "adults": adults,
            "currency": currency,
            "date_range": f"{start_date.isoformat()}_{end_date.isoformat()}"
        }

    async def _fetch_cheapest_price_async(
        self,
        origin: str,
        destination: str,
        start_date: date,
        end_date: date,
        adults: int,
        currency: str
    ) -> Optional[dict]:
        """
        Fetch cheapest price for a single origin-destination pair over date range.

        Uses getCalendarPicker API to get prices for all dates, returns minimum with date.

        Returns:
            {"price": float, "date": str} or None if no flights available
        """
        params = {
            "departure_id": origin,
            "arrival_id": destination,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "adults": str(adults),
            "trip_type": "ONE_WAY",
            "travel_class": "ECONOMY",
            "currency": currency,
            "country_code": "US",
        }

        try:
            logger.info(f"Calling getCalendarPicker: {origin} -> {destination}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/getCalendarPicker",
                    headers=self._headers,
                    params=params
                )

                logger.info(f"Response status: {response.status_code} for {origin} -> {destination}")

                if response.status_code != 200:
                    logger.error(f"HTTP {response.status_code}: {response.text[:500]}")
                    return None

                data = response.json()

            # Check API response status
            if not data.get("status"):
                logger.warning(f"API error for {origin} -> {destination}: {data.get('message')}")
                return None

            # Extract prices and find minimum with its date
            api_data = data.get("data", [])
            logger.info(f"Got {len(api_data)} price entries for {origin} -> {destination}")

            if not api_data:
                return None

            # Filter valid entries and find the cheapest
            valid_entries = [
                item for item in api_data
                if item.get("price") is not None and item.get("departure")
            ]

            if not valid_entries:
                logger.warning(f"No valid price entries for {origin} -> {destination}")
                return None

            # Find the entry with minimum price
            cheapest = min(valid_entries, key=lambda x: x["price"])

            result = {
                "price": cheapest["price"],
                "date": cheapest["departure"]  # Format: "YYYY-MM-DD"
            }

            # Save to MongoDB for historical data
            await self._save_flight_prices_to_mongo(
                origin=origin,
                destination=destination,
                adults=adults,
                currency=currency,
                cheapest_price=result,
                all_prices=valid_entries
            )

            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {origin} -> {destination}: {e.response.status_code} - {e.response.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"Error fetching price {origin} -> {destination}: {e}", exc_info=True)
            return None

    async def _save_flight_prices_to_mongo(
        self,
        origin: str,
        destination: str,
        adults: int,
        currency: str,
        cheapest_price: dict,
        all_prices: list[dict]
    ) -> None:
        """
        Save flight price data to MongoDB for historical analysis.

        Creates/updates a document with:
        - Route info (origin, destination)
        - Current cheapest price
        - All available prices from the API
        - Timestamp of the fetch
        """
        if not self._mongo:
            return

        try:
            db = self._mongo.client[self._mongo._settings.mongodb_db]
            collection = db["flight_prices"]

            doc = {
                "route_key": f"{origin}_{destination}",
                "origin": origin,
                "destination": destination,
                "adults": adults,
                "currency": currency,
                "cheapest_price": cheapest_price["price"],
                "cheapest_date": cheapest_price["date"],
                "all_prices": all_prices,
                "fetched_at": datetime.utcnow(),
                "prices_count": len(all_prices)
            }

            # Upsert: update if exists, insert if not
            await collection.update_one(
                {"route_key": f"{origin}_{destination}", "currency": currency},
                {"$set": doc},
                upsert=True
            )

            logger.debug(f"Saved to MongoDB: {origin} -> {destination} ({len(all_prices)} prices)")

        except Exception as e:
            # Don't fail the main operation if MongoDB save fails
            logger.error(f"Failed to save to MongoDB: {e}")
