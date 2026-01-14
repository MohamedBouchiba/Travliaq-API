"""Service for caching flight prices by country with MongoDB persistence."""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional, Literal

if TYPE_CHECKING:
    from app.db.mongo import MongoManager
    from app.services.flights import FlightsService
    from app.services.airports import AirportsService

logger = logging.getLogger(__name__)

# Type alias for price sources
PriceSource = Literal["cache", "api", "estimated"]


# Mapping of country codes to their main international airports
COUNTRY_MAIN_AIRPORTS = {
    # Europe
    "FR": "CDG",  # France - Paris Charles de Gaulle
    "ES": "MAD",  # Spain - Madrid Barajas
    "IT": "FCO",  # Italy - Rome Fiumicino
    "PT": "LIS",  # Portugal - Lisbon
    "DE": "FRA",  # Germany - Frankfurt
    "GB": "LHR",  # UK - London Heathrow
    "NL": "AMS",  # Netherlands - Amsterdam Schiphol
    "BE": "BRU",  # Belgium - Brussels
    "AT": "VIE",  # Austria - Vienna
    "CH": "ZRH",  # Switzerland - Zurich
    "GR": "ATH",  # Greece - Athens
    "HR": "ZAG",  # Croatia - Zagreb
    "CZ": "PRG",  # Czech Republic - Prague
    "PL": "WAW",  # Poland - Warsaw
    "HU": "BUD",  # Hungary - Budapest
    "IE": "DUB",  # Ireland - Dublin
    "DK": "CPH",  # Denmark - Copenhagen
    "SE": "ARN",  # Sweden - Stockholm Arlanda
    "NO": "OSL",  # Norway - Oslo
    "FI": "HEL",  # Finland - Helsinki
    "RO": "OTP",  # Romania - Bucharest
    "SK": "BTS",  # Slovakia - Bratislava
    "SI": "LJU",  # Slovenia - Ljubljana
    "BA": "SJJ",  # Bosnia-Herzegovina - Sarajevo
    "LU": "LUX",  # Luxembourg
    "LV": "RIX",  # Latvia - Riga
    # Asia
    "TH": "BKK",  # Thailand - Bangkok Suvarnabhumi
    "VN": "SGN",  # Vietnam - Ho Chi Minh City
    "JP": "NRT",  # Japan - Tokyo Narita
    "KR": "ICN",  # South Korea - Seoul Incheon
    "CN": "PEK",  # China - Beijing
    "HK": "HKG",  # Hong Kong
    "SG": "SIN",  # Singapore - Changi
    "MY": "KUL",  # Malaysia - Kuala Lumpur
    "ID": "DPS",  # Indonesia - Bali Denpasar
    "PH": "MNL",  # Philippines - Manila
    "IN": "DEL",  # India - New Delhi
    "LK": "CMB",  # Sri Lanka - Colombo
    "NP": "KTM",  # Nepal - Kathmandu
    "AE": "DXB",  # UAE - Dubai
    "TR": "IST",  # Turkey - Istanbul
    "IL": "TLV",  # Israel - Tel Aviv
    "JO": "AMM",  # Jordan - Amman
    "TW": "TPE",  # Taiwan - Taipei
    "LA": "VTE",  # Laos - Vientiane
    "MM": "RGN",  # Myanmar - Yangon
    "UZ": "TAS",  # Uzbekistan - Tashkent
    "KZ": "NQZ",  # Kazakhstan - Nursultan (Astana)
    "SA": "RUH",  # Saudi Arabia - Riyadh
    "OM": "MCT",  # Oman - Muscat
    "QA": "DOH",  # Qatar - Doha
    "BH": "BAH",  # Bahrain
    # Americas
    "US": "JFK",  # USA - New York JFK
    "CA": "YYZ",  # Canada - Toronto
    "MX": "MEX",  # Mexico - Mexico City
    "BR": "GRU",  # Brazil - Sao Paulo
    "AR": "EZE",  # Argentina - Buenos Aires
    "CL": "SCL",  # Chile - Santiago
    "PE": "LIM",  # Peru - Lima
    "CO": "BOG",  # Colombia - Bogota
    "CR": "SJO",  # Costa Rica - San Jose
    "PA": "PTY",  # Panama - Panama City
    "CU": "HAV",  # Cuba - Havana
    "DO": "PUJ",  # Dominican Republic - Punta Cana
    "JM": "MBJ",  # Jamaica - Montego Bay
    "EC": "UIO",  # Ecuador - Quito
    "BO": "LPB",  # Bolivia - La Paz
    "UY": "MVD",  # Uruguay - Montevideo
    "GT": "GUA",  # Guatemala - Guatemala City
    "HN": "SAP",  # Honduras - San Pedro Sula
    "NI": "MGA",  # Nicaragua - Managua
    # Africa
    "MA": "CMN",  # Morocco - Casablanca
    "EG": "CAI",  # Egypt - Cairo
    "ZA": "JNB",  # South Africa - Johannesburg
    "KE": "NBO",  # Kenya - Nairobi
    "TZ": "DAR",  # Tanzania - Dar es Salaam
    "TN": "TUN",  # Tunisia - Tunis
    "MU": "MRU",  # Mauritius
    "SC": "SEZ",  # Seychelles - Mahe
    "SN": "DSS",  # Senegal - Dakar
    "GH": "ACC",  # Ghana - Accra
    "RW": "KGL",  # Rwanda - Kigali
    "UG": "EBB",  # Uganda - Entebbe
    "ET": "ADD",  # Ethiopia - Addis Ababa
    "NA": "WDH",  # Namibia - Windhoek
    "BW": "GBE",  # Botswana - Gaborone
    "MZ": "MPM",  # Mozambique - Maputo
    "MG": "TNR",  # Madagascar - Antananarivo
    # Oceania
    "AU": "SYD",  # Australia - Sydney
    "NZ": "AKL",  # New Zealand - Auckland
    "FJ": "NAN",  # Fiji - Nadi
    "PF": "PPT",  # French Polynesia - Tahiti
    "WS": "APW",  # Samoa - Apia
    "VU": "VLI",  # Vanuatu - Port Vila
    "NC": "NOU",  # New Caledonia - Noumea
    "TO": "TBU",  # Tonga - Tongatapu
    # Caribbean & Islands
    "MV": "MLE",  # Maldives - Male
    "CY": "LCA",  # Cyprus - Larnaca
    "MT": "MLA",  # Malta
    "IS": "KEF",  # Iceland - Reykjavik Keflavik
    "CV": "SID",  # Cape Verde - Sal
}


# Main airport coordinates for distance estimation (lat, lon)
# Used for distance-based price estimation when API doesn't return a price
# These are derived from the COUNTRY_MAIN_AIRPORTS mapping above
AIRPORT_COORDINATES = {
    # Europe
    "CDG": (49.0097, 2.5479),  # Paris Charles de Gaulle
    "MAD": (40.4983, -3.5676),  # Madrid Barajas
    "FCO": (41.8003, 12.2389),  # Rome Fiumicino
    "LIS": (38.7813, -9.1359),  # Lisbon
    "FRA": (50.0379, 8.5622),  # Frankfurt
    "LHR": (51.4700, -0.4543),  # London Heathrow
    "AMS": (52.3105, 4.7683),  # Amsterdam Schiphol
    "ATH": (37.9364, 23.9445),  # Athens
    "VIE": (48.1103, 16.5697),  # Vienna
    "ZRH": (47.4647, 8.5492),  # Zurich
    "BRU": (50.9014, 4.4844),  # Brussels
    "PRG": (50.1008, 14.2600),  # Prague
    "WAW": (52.1657, 20.9671),  # Warsaw
    "BUD": (47.4369, 19.2556),  # Budapest
    "DUB": (53.4264, -6.2499),  # Dublin
    "CPH": (55.6180, 12.6508),  # Copenhagen
    "ARN": (59.6519, 17.9186),  # Stockholm Arlanda
    "OSL": (60.1939, 11.1004),  # Oslo
    "HEL": (60.3172, 24.9633),  # Helsinki
    "IST": (41.2753, 28.7519),  # Istanbul
    "ZAG": (45.7430, 16.0688),  # Zagreb Croatia
    "OTP": (44.5711, 26.0850),  # Bucharest Romania
    "BTS": (48.1702, 17.2127),  # Bratislava Slovakia
    "LJU": (46.2237, 14.4576),  # Ljubljana Slovenia
    "SJJ": (43.8246, 18.3315),  # Sarajevo Bosnia
    "LUX": (49.6233, 6.2044),   # Luxembourg
    "RIX": (56.9236, 23.9711),  # Riga Latvia
    # Asia
    "BKK": (13.6900, 100.7501),  # Bangkok Suvarnabhumi
    "SGN": (10.8188, 106.6520),  # Ho Chi Minh City
    "NRT": (35.7720, 140.3929),  # Tokyo Narita
    "ICN": (37.4602, 126.4407),  # Seoul Incheon
    "PEK": (40.0799, 116.6031),  # Beijing
    "HKG": (22.3080, 113.9185),  # Hong Kong
    "SIN": (1.3644, 103.9915),  # Singapore Changi
    "KUL": (2.7456, 101.7099),  # Kuala Lumpur
    "DPS": (-8.7482, 115.1675),  # Bali Denpasar
    "MNL": (14.5086, 121.0198),  # Manila
    "DEL": (28.5562, 77.1000),  # New Delhi
    "CMB": (7.1808, 79.8841),  # Colombo
    "KTM": (27.6966, 85.3591),  # Kathmandu
    "DXB": (25.2532, 55.3657),  # Dubai
    "TLV": (32.0055, 34.8854),  # Tel Aviv
    "AMM": (31.7226, 35.9932),  # Amman
    "TPE": (25.0797, 121.2342),  # Taipei Taiwan
    "VTE": (17.9883, 102.5633),  # Vientiane Laos
    "RGN": (16.9073, 96.1332),   # Yangon Myanmar
    "TAS": (41.2579, 69.2817),   # Tashkent Uzbekistan
    "NQZ": (51.0222, 71.4669),   # Nursultan Kazakhstan
    "RUH": (24.9576, 46.6988),   # Riyadh Saudi Arabia
    "MCT": (23.5933, 58.2844),   # Muscat Oman
    "DOH": (25.2731, 51.6081),   # Doha Qatar
    "BAH": (26.2708, 50.6336),   # Bahrain
    # Americas
    "JFK": (40.6413, -73.7781),  # New York JFK
    "YYZ": (43.6777, -79.6248),  # Toronto
    "MEX": (19.4363, -99.0721),  # Mexico City
    "GRU": (-23.4356, -46.4731),  # Sao Paulo
    "EZE": (-34.8222, -58.5358),  # Buenos Aires
    "SCL": (-33.3930, -70.7858),  # Santiago
    "LIM": (-12.0219, -77.1143),  # Lima
    "BOG": (4.7016, -74.1469),  # Bogota
    "SJO": (9.9939, -84.2088),  # San Jose Costa Rica
    "HAV": (22.9892, -82.4091),  # Havana
    "PUJ": (18.5674, -68.3634),  # Punta Cana
    "PTY": (9.0714, -79.3835),   # Panama City Tocumen
    "MBJ": (18.5037, -77.9134),  # Montego Bay Jamaica
    "UIO": (-0.1292, -78.3575),   # Quito Ecuador
    "LPB": (-16.5133, -68.1922),  # La Paz Bolivia
    "MVD": (-34.8381, -56.0308),  # Montevideo Uruguay
    "GUA": (14.5833, -90.5275),   # Guatemala City
    "SAP": (15.4526, -87.9236),   # San Pedro Sula Honduras
    "MGA": (12.1415, -86.1682),   # Managua Nicaragua
    # Africa
    "CMN": (33.3675, -7.5899),  # Casablanca
    "CAI": (30.1219, 31.4056),  # Cairo
    "JNB": (-26.1392, 28.2460),  # Johannesburg
    "NBO": (-1.3192, 36.9278),  # Nairobi
    "TUN": (36.8510, 10.2272),  # Tunis
    "MRU": (-20.4302, 57.6836),  # Mauritius
    "SEZ": (-4.6743, 55.5218),  # Seychelles
    "DAR": (-6.8781, 39.2026),  # Dar es Salaam Tanzania
    "DSS": (14.7397, -17.4902), # Dakar Senegal
    "SID": (16.7414, -22.9494), # Sal Cape Verde
    "ACC": (5.6052, -0.1668),   # Accra Ghana
    "KGL": (-1.9686, 30.1395),  # Kigali Rwanda
    "EBB": (0.0424, 32.4435),   # Entebbe Uganda
    "ADD": (8.9779, 38.7993),   # Addis Ababa Ethiopia
    "WDH": (-22.4799, 17.4709), # Windhoek Namibia
    "GBE": (-24.5553, 25.9181), # Gaborone Botswana
    "MPM": (-25.9208, 32.5726), # Maputo Mozambique
    "TNR": (-18.7969, 47.4788), # Antananarivo Madagascar
    # Oceania & Islands
    "SYD": (-33.9399, 151.1753),  # Sydney
    "AKL": (-37.0082, 174.7850),  # Auckland
    "NAN": (-17.7554, 177.4434),  # Fiji Nadi
    "PPT": (-17.5537, -149.6068),  # Tahiti Papeete
    "APW": (-13.8297, -171.9972), # Apia Samoa
    "VLI": (-17.6993, 168.3199),  # Port Vila Vanuatu
    "NOU": (-22.0146, 166.2129),  # Noumea New Caledonia
    "TBU": (-21.2411, -175.1497), # Tongatapu Tonga
    "MLE": (4.1918, 73.5290),  # Maldives Male
    "LCA": (34.8751, 33.6249),  # Larnaca Cyprus
    "MLA": (35.8575, 14.4775),  # Malta
    "KEF": (63.9850, -22.6056),  # Iceland Keflavik
}

# Distance-based price estimation matrix (max_distance_km, base_price_eur)
DISTANCE_PRICE_BRACKETS = [
    (1500, 120),    # Short haul Europe (< 1500 km)
    (3000, 200),    # Medium haul (1500-3000 km)
    (5000, 400),    # Long haul (3000-5000 km)
    (8000, 600),    # Very long haul (5000-8000 km)
    (12000, 800),   # Ultra long haul (8000-12000 km)
    (float("inf"), 1000),  # Maximum distance
]

# Base regional price multipliers (relative to distance-based calculation)
# Used to adjust estimates based on typical route pricing patterns
# These are multipliers, not absolute prices - actual prices come from distance calculation
REGIONAL_PRICE_FACTORS = {
    "Europe": 0.9,  # Generally well-connected, competitive pricing
    "Western Europe": 0.85,
    "Southern Europe": 0.9,
    "Eastern Europe": 0.95,
    "Northern Europe": 1.0,
    "Asia": 1.1,  # Longer flights but competitive
    "Southeast Asia": 1.0,  # Budget airlines available
    "East Asia": 1.15,
    "South Asia": 0.95,
    "Middle East": 1.05,  # Hub airports, good connectivity
    "North America": 1.1,
    "South America": 1.2,  # Less competition
    "Central America": 1.15,
    "Caribbean": 1.1,  # Resort pricing
    "Africa": 1.25,  # Less competition, fewer routes
    "North Africa": 0.95,  # Close to Europe
    "Sub-Saharan Africa": 1.3,
    "Oceania": 1.2,  # Long distances
    "Pacific Islands": 1.35,  # Remote, limited routes
}


class FlightPriceCacheService:
    """
    Service for managing cached flight prices per country.

    Uses MongoDB for persistent storage with TTL-based expiration.
    Falls back to FlightsService API when cache misses occur.
    """

    CACHE_TTL_DAYS = 7
    COLLECTION_NAME = "flight_price_averages"

    def __init__(
        self,
        mongo_manager: "MongoManager",
        flights_service: Optional["FlightsService"],
        airports_service: Optional["AirportsService"],
    ):
        """
        Initialize the flight price cache service.

        Args:
            mongo_manager: MongoDB manager for persistent storage
            flights_service: Flights service for API calls (optional)
            airports_service: Airports service for resolving city to IATA (optional)
        """
        self._mongo = mongo_manager
        self._flights = flights_service
        self._airports = airports_service

    async def get_flight_price(
        self,
        origin_city: str,
        destination_country_code: str,
        currency: str = "EUR",
    ) -> Optional[int]:
        """
        Get average round-trip flight price to a country.

        Uses cached price if available and not expired,
        otherwise fetches from API and caches the result.

        Args:
            origin_city: User's departure city name
            destination_country_code: ISO2 country code of destination
            currency: Currency for prices (default: EUR)

        Returns:
            Average round-trip price in specified currency, or None if unavailable
        """
        if not self._flights:
            logger.debug("FlightsService not available, skipping flight price fetch")
            return None

        # 1. Resolve origin airport from city name
        origin_iata = await self._resolve_origin_airport(origin_city)
        if not origin_iata:
            logger.debug(f"Could not resolve airport for city: {origin_city}")
            return None

        # 2. Get main airport for destination country
        dest_iata = COUNTRY_MAIN_AIRPORTS.get(destination_country_code.upper())
        if not dest_iata:
            logger.debug(f"No main airport defined for country: {destination_country_code}")
            return None

        # 3. Check MongoDB cache
        cached = await self._get_cached_price(origin_iata, destination_country_code)
        if cached:
            logger.debug(
                f"Cache HIT: {origin_iata} -> {destination_country_code} = {cached['avg_price_eur']} EUR"
            )
            return cached["avg_price_eur"]

        # 4. Fetch from API and cache
        logger.info(f"Cache MISS: Fetching price {origin_iata} -> {dest_iata}")
        price_data = await self._fetch_and_cache_price(
            origin_iata, dest_iata, destination_country_code, currency
        )

        return price_data["avg_price_eur"] if price_data else None

    async def get_flight_prices_batch(
        self,
        origin_city: str,
        destination_country_codes: list[str],
        currency: str = "EUR",
    ) -> dict[str, Optional[int]]:
        """
        Get flight prices for multiple destinations efficiently.

        Args:
            origin_city: User's departure city name
            destination_country_codes: List of ISO2 country codes
            currency: Currency for prices (default: EUR)

        Returns:
            Dict mapping country codes to prices (None if unavailable)
        """
        if not self._flights:
            return {code: None for code in destination_country_codes}

        # Resolve origin airport
        origin_iata = await self._resolve_origin_airport(origin_city)
        if not origin_iata:
            return {code: None for code in destination_country_codes}

        results: dict[str, Optional[int]] = {}
        to_fetch: list[tuple[str, str]] = []  # (country_code, dest_iata)

        # Check cache for each destination
        for country_code in destination_country_codes:
            dest_iata = COUNTRY_MAIN_AIRPORTS.get(country_code.upper())
            if not dest_iata:
                results[country_code] = None
                continue

            cached = await self._get_cached_price(origin_iata, country_code)
            if cached:
                results[country_code] = cached["avg_price_eur"]
            else:
                to_fetch.append((country_code, dest_iata))

        # Batch fetch missing prices using get_map_prices
        if to_fetch and self._flights:
            dest_iatas = [d[1] for d in to_fetch]
            try:
                prices_data, _, _ = await self._flights.get_map_prices(
                    origin=origin_iata,
                    destinations=dest_iatas,
                    adults=1,
                    currency=currency,
                )

                # Process and cache results
                for country_code, dest_iata in to_fetch:
                    price_info = prices_data.get(dest_iata)
                    if price_info:
                        # Calculate round-trip price (aller × 1.8)
                        round_trip_price = int(price_info["price"] * 1.8)
                        results[country_code] = round_trip_price

                        # Cache the result
                        await self._save_to_cache(
                            origin_iata=origin_iata,
                            destination_country=country_code,
                            destination_iata=dest_iata,
                            avg_price_eur=round_trip_price,
                            min_price_eur=int(price_info["price"]),
                            currency=currency,
                        )
                    else:
                        results[country_code] = None

            except Exception as e:
                logger.error(f"Error fetching batch prices: {e}")
                for country_code, _ in to_fetch:
                    if country_code not in results:
                        results[country_code] = None

        return results

    async def _resolve_origin_airport(self, city: str) -> Optional[str]:
        """
        Resolve a city name to its nearest airport IATA code.

        Args:
            city: City name

        Returns:
            IATA code of nearest airport, or None if not found
        """
        if not self._airports:
            logger.debug("AirportsService not available")
            return None

        try:
            result = self._airports.find_nearest_airports(city_query=city, limit=1)
            if result and result.airports:
                return result.airports[0].iata
        except Exception as e:
            logger.warning(f"Error resolving airport for {city}: {e}")

        return None

    async def _resolve_origin_airport_with_coords(
        self, city: str
    ) -> Optional[tuple[str, float, float]]:
        """
        Resolve a city name to its nearest airport IATA code with coordinates.

        Args:
            city: City name

        Returns:
            Tuple of (IATA code, lat, lon) or None if not found
        """
        if not self._airports:
            logger.debug("AirportsService not available")
            return None

        try:
            result = self._airports.find_nearest_airports(city_query=city, limit=1)
            if result and result.airports:
                airport = result.airports[0]
                return airport.iata, airport.lat, airport.lon
        except Exception as e:
            logger.warning(f"Error resolving airport for {city}: {e}")

        return None

    async def _get_cached_price(
        self, origin_iata: str, destination_country: str
    ) -> Optional[dict]:
        """
        Get cached price from MongoDB if not expired.

        Args:
            origin_iata: Origin airport IATA code
            destination_country: Destination country ISO2 code

        Returns:
            Cached document if valid, None otherwise
        """
        try:
            db = self._mongo.client[self._mongo._settings.mongodb_db]
            collection = db[self.COLLECTION_NAME]

            doc = await collection.find_one(
                {
                    "origin_iata": origin_iata,
                    "destination_country": destination_country.upper(),
                    "expires_at": {"$gt": datetime.utcnow()},
                }
            )

            return doc
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None

    async def _fetch_and_cache_price(
        self,
        origin_iata: str,
        dest_iata: str,
        country_code: str,
        currency: str,
    ) -> Optional[dict]:
        """
        Fetch price from API and cache in MongoDB.

        Args:
            origin_iata: Origin airport IATA code
            dest_iata: Destination airport IATA code
            country_code: Destination country ISO2 code
            currency: Currency code

        Returns:
            Price document if successful, None otherwise
        """
        if not self._flights:
            return None

        try:
            prices_data, _, _ = await self._flights.get_map_prices(
                origin=origin_iata,
                destinations=[dest_iata],
                adults=1,
                currency=currency,
            )

            price_info = prices_data.get(dest_iata)
            if not price_info:
                logger.info(f"No flights found: {origin_iata} -> {dest_iata}")
                return None

            # Calculate round-trip price (aller × 1.8 approximation)
            round_trip_price = int(price_info["price"] * 1.8)

            # Save to cache
            doc = await self._save_to_cache(
                origin_iata=origin_iata,
                destination_country=country_code,
                destination_iata=dest_iata,
                avg_price_eur=round_trip_price,
                min_price_eur=int(price_info["price"]),
                currency=currency,
            )

            logger.info(
                f"Cached: {origin_iata} -> {country_code} = {round_trip_price} EUR (round-trip)"
            )

            return doc

        except Exception as e:
            logger.error(f"Error fetching price {origin_iata} -> {dest_iata}: {e}")
            return None

    async def _save_to_cache(
        self,
        origin_iata: str,
        destination_country: str,
        destination_iata: str,
        avg_price_eur: int,
        min_price_eur: int,
        currency: str,
    ) -> dict:
        """
        Save flight price to MongoDB cache.

        Args:
            origin_iata: Origin airport IATA code
            destination_country: Destination country ISO2 code
            destination_iata: Destination airport IATA code
            avg_price_eur: Average round-trip price
            min_price_eur: Minimum one-way price found
            currency: Currency code

        Returns:
            Saved document
        """
        now = datetime.utcnow()
        doc = {
            "origin_iata": origin_iata,
            "destination_country": destination_country.upper(),
            "destination_iata": destination_iata,
            "avg_price_eur": avg_price_eur,
            "min_price_eur": min_price_eur,
            "currency": currency,
            "trip_type": "ROUND",
            "fetched_at": now,
            "expires_at": now + timedelta(days=self.CACHE_TTL_DAYS),
        }

        try:
            db = self._mongo.client[self._mongo._settings.mongodb_db]
            collection = db[self.COLLECTION_NAME]

            # Upsert: update if exists, insert if not
            await collection.update_one(
                {
                    "origin_iata": origin_iata,
                    "destination_country": destination_country.upper(),
                },
                {"$set": doc},
                upsert=True,
            )

        except Exception as e:
            logger.error(f"Error saving to cache: {e}")

        return doc

    async def invalidate_cache(
        self, origin_iata: Optional[str] = None, destination_country: Optional[str] = None
    ) -> int:
        """
        Invalidate cached prices.

        Args:
            origin_iata: Optional origin to filter by
            destination_country: Optional destination to filter by

        Returns:
            Number of documents deleted
        """
        try:
            db = self._mongo.client[self._mongo._settings.mongodb_db]
            collection = db[self.COLLECTION_NAME]

            query = {}
            if origin_iata:
                query["origin_iata"] = origin_iata
            if destination_country:
                query["destination_country"] = destination_country.upper()

            result = await collection.delete_many(query)
            return result.deleted_count

        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return 0

    # =========================================================================
    # GUARANTEED PRICE WITH FALLBACKS
    # =========================================================================

    async def get_flight_price_with_fallbacks(
        self,
        origin_city: str,
        destination_country_code: str,
        destination_profile: Optional[dict] = None,
        currency: str = "EUR",
    ) -> tuple[int, PriceSource]:
        """
        Get flight price with GUARANTEED result using multiple sources.

        Always returns a price, using the following priority:
        1. MongoDB Cache (if available and not expired)
        2. API call to Google Flights (get_map_prices)
        3. Distance-based estimation with regional adjustments

        Args:
            origin_city: User's departure city name
            destination_country_code: ISO2 country code of destination
            destination_profile: Country profile dict (for region/budget info)
            currency: Currency for prices (default: EUR)

        Returns:
            Tuple of (price_in_eur, source) where source indicates
            how the price was obtained
        """
        country_code = destination_country_code.upper()

        # Resolve origin airport with coordinates using find_nearest_airports endpoint
        origin_data = await self._resolve_origin_airport_with_coords(origin_city)
        origin_iata = origin_data[0] if origin_data else None
        origin_coords = (origin_data[1], origin_data[2]) if origin_data else None
        dest_iata = COUNTRY_MAIN_AIRPORTS.get(country_code)

        # === SOURCE 1: MongoDB Cache ===
        if origin_iata:
            cached = await self._get_cached_price(origin_iata, country_code)
            if cached:
                logger.debug(f"Price from cache: {origin_iata} -> {country_code} = {cached['avg_price_eur']} EUR")
                return cached["avg_price_eur"], "cache"

        # === SOURCE 2: API Call (Google Flights) ===
        if origin_iata and dest_iata:
            price_data = await self._fetch_and_cache_price(
                origin_iata, dest_iata, country_code, currency
            )
            if price_data:
                logger.debug(f"Price from API: {origin_iata} -> {country_code} = {price_data['avg_price_eur']} EUR")
                return price_data["avg_price_eur"], "api"

        # === SOURCE 3: Distance-based Estimation ===
        # Uses coordinates from find_nearest_airports for accurate distance calculation
        estimated = self._estimate_price_by_distance(
            origin_city, country_code, destination_profile, origin_coords
        )
        logger.debug(f"Price estimated: {origin_city} -> {country_code} = {estimated} EUR")
        return estimated, "estimated"

    async def get_flight_prices_batch_with_fallbacks(
        self,
        origin_city: str,
        destination_country_codes: list[str],
        destination_profiles: dict[str, dict],
        currency: str = "EUR",
    ) -> tuple[dict[str, tuple[int, PriceSource]], str | None]:
        """
        Get flight prices for multiple destinations with guaranteed results.

        Args:
            origin_city: User's departure city name
            destination_country_codes: List of ISO2 country codes
            destination_profiles: Dict mapping country codes to profiles
            currency: Currency for prices (default: EUR)

        Returns:
            Tuple of:
            - Dict mapping country codes to (price, source) tuples
            - Origin airport IATA code used for price estimation (or None)
        """
        results: dict[str, tuple[int, PriceSource]] = {}

        # Resolve origin airport with coordinates once using find_nearest_airports
        origin_data = await self._resolve_origin_airport_with_coords(origin_city)
        origin_iata = origin_data[0] if origin_data else None
        origin_coords = (origin_data[1], origin_data[2]) if origin_data else None

        # Separate destinations by whether we can query the API or need estimation
        to_check_cache: list[str] = []
        to_fetch_api: list[tuple[str, str]] = []  # (country_code, dest_iata)

        for country_code in destination_country_codes:
            code = country_code.upper()
            dest_iata = COUNTRY_MAIN_AIRPORTS.get(code)

            if origin_iata and dest_iata:
                to_check_cache.append(code)
            else:
                # No airport mapping - use distance estimation
                profile = destination_profiles.get(code, {})
                estimated = self._estimate_price_by_distance(
                    origin_city, code, profile, origin_coords
                )
                results[code] = (estimated, "estimated")

        # Check cache for all API-capable destinations
        for country_code in to_check_cache:
            cached = await self._get_cached_price(origin_iata, country_code)
            if cached:
                results[country_code] = (cached["avg_price_eur"], "cache")
            else:
                dest_iata = COUNTRY_MAIN_AIRPORTS.get(country_code)
                if dest_iata:
                    to_fetch_api.append((country_code, dest_iata))

        # Batch fetch from API for cache misses
        if to_fetch_api and origin_iata and self._flights:
            dest_iatas = [d[1] for d in to_fetch_api]
            prices_data, _, _ = await self._flights.get_map_prices(
                origin=origin_iata,
                destinations=dest_iatas,
                adults=1,
                currency=currency,
            )

            for country_code, dest_iata in to_fetch_api:
                price_info = prices_data.get(dest_iata)
                if price_info:
                    round_trip_price = int(price_info["price"] * 1.8)
                    results[country_code] = (round_trip_price, "api")

                    # Cache the result
                    await self._save_to_cache(
                        origin_iata=origin_iata,
                        destination_country=country_code,
                        destination_iata=dest_iata,
                        avg_price_eur=round_trip_price,
                        min_price_eur=int(price_info["price"]),
                        currency=currency,
                    )
                else:
                    # API didn't return price for this destination - use estimation
                    profile = destination_profiles.get(country_code, {})
                    estimated = self._estimate_price_by_distance(
                        origin_city, country_code, profile, origin_coords
                    )
                    results[country_code] = (estimated, "estimated")
        elif to_fetch_api:
            # FlightsService not available - fallback to estimation for all
            for country_code, dest_iata in to_fetch_api:
                profile = destination_profiles.get(country_code, {})
                estimated = self._estimate_price_by_distance(
                    origin_city, country_code, profile, origin_coords
                )
                results[country_code] = (estimated, "estimated")

        return results, origin_iata

    def _estimate_price_by_distance(
        self,
        origin_city: str,
        country_code: str,
        profile: Optional[dict] = None,
        origin_coords: Optional[tuple[float, float]] = None,
    ) -> int:
        """
        Estimate flight price based on distance between origin and destination airports.

        Uses Haversine formula to calculate great-circle distance,
        then maps to price brackets with regional and cost-of-living adjustments.

        Args:
            origin_city: Origin city name (used for logging)
            country_code: Destination country ISO2 code
            profile: Country profile dict (for region and cost-of-living data)
            origin_coords: Optional (lat, lon) of origin airport (from find_nearest_airports)

        Returns:
            Estimated round-trip price in EUR
        """
        # Get destination airport IATA and coordinates
        dest_iata = COUNTRY_MAIN_AIRPORTS.get(country_code.upper())
        dest_coords = AIRPORT_COORDINATES.get(dest_iata) if dest_iata else None

        if not dest_coords:
            # No airport data - use regional average based on profile
            if profile:
                region = profile.get("region", "")
                subregion = profile.get("subregion", "")
                # Calculate based on typical regional distances from Europe
                regional_distances = {
                    "Europe": 1000,
                    "Asia": 8000,
                    "North America": 6500,
                    "South America": 10000,
                    "Africa": 4500,
                    "Oceania": 16000,
                }
                distance_km = regional_distances.get(region, 5000)
            else:
                distance_km = 5000  # Default medium-long haul

            # Map distance to price
            base_price = 400
            for max_dist, price in DISTANCE_PRICE_BRACKETS:
                if distance_km <= max_dist:
                    base_price = price
                    break
            return base_price

        # Use provided origin coordinates or fallback to Paris CDG
        if not origin_coords:
            # Default to Paris CDG coordinates
            origin_coords = AIRPORT_COORDINATES.get("CDG", (49.0097, 2.5479))

        # Calculate distance using Haversine formula
        distance_km = self._haversine_distance(origin_coords, dest_coords)

        # Map distance to price bracket
        base_price = 400  # Default
        for max_dist, price in DISTANCE_PRICE_BRACKETS:
            if distance_km <= max_dist:
                base_price = price
                break

        # Apply regional price factor
        if profile:
            region = profile.get("region", "")
            subregion = profile.get("subregion", "")
            # Try subregion first, then region, default to 1.0
            factor = REGIONAL_PRICE_FACTORS.get(subregion) or REGIONAL_PRICE_FACTORS.get(region, 1.0)
            base_price = int(base_price * factor)

            # Additional adjustment for cost of living (±15%)
            col_index = profile.get("budget", {}).get("cost_of_living_index", 100)
            # COL 50 = -7.5%, COL 150 = +7.5%
            col_adjustment = 1 + (col_index - 100) * 0.0015
            base_price = int(base_price * col_adjustment)

        logger.debug(
            f"Estimated price {origin_city} -> {country_code}: "
            f"distance={distance_km:.0f}km, price={base_price} EUR"
        )

        return base_price

    @staticmethod
    def _haversine_distance(
        coord1: tuple[float, float], coord2: tuple[float, float]
    ) -> float:
        """
        Calculate great-circle distance between two points using Haversine formula.

        Args:
            coord1: (latitude, longitude) of first point
            coord2: (latitude, longitude) of second point

        Returns:
            Distance in kilometers
        """
        lat1, lon1 = coord1
        lat2, lon2 = coord2

        # Earth's radius in kilometers
        R = 6371

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        # Haversine formula
        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
