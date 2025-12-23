"""Service for finding nearest airports to a city."""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Optional, Tuple

from rapidfuzz import fuzz

from app.models.airports import AirportResult, NearestAirportsResponse

if TYPE_CHECKING:
    from app.db.postgres import PostgresManager

logger = logging.getLogger(__name__)


class AirportsService:
    """Service for finding nearest airports to a city."""

    def __init__(self, postgres_manager: PostgresManager):
        self._postgres = postgres_manager

    def find_nearest_airports(
        self,
        city_query: str,
        limit: int = 3
    ) -> Optional[NearestAirportsResponse]:
        """
        Find nearest airports to a city using fuzzy matching and geographic distance.

        Args:
            city_query: City name (can contain typos)
            limit: Maximum number of airports to return

        Returns:
            NearestAirportsResponse with matched city and nearest airports
            None if no city match found

        Strategy:
        1. Find best matching city using fuzzy matching (>80% similarity)
        2. Use PostGIS ST_Distance to find nearest airports
        3. Return sorted by distance
        """
        city_query = city_query.strip()

        if len(city_query) < 2:
            logger.warning(f"City query too short: '{city_query}'")
            return None

        conn = None
        try:
            conn = self._postgres.get_connection()

            # Step 1: Find best matching city using fuzzy matching
            city_match = self._find_best_city_match(conn, city_query)

            if not city_match:
                logger.info(f"No city match found for query: '{city_query}'")
                return None

            city_id, city_name, city_lat, city_lon, match_score = city_match

            logger.info(
                f"Matched '{city_query}' to '{city_name}' "
                f"(score: {match_score}, id: {city_id})"
            )

            # Step 2: Find nearest airports using PostGIS distance
            airports = self._find_nearest_airports_to_location(
                conn,
                city_lat,
                city_lon,
                limit
            )

            return NearestAirportsResponse(
                city_query=city_query,
                matched_city=city_name,
                matched_city_id=city_id,
                match_score=match_score,
                city_location={"lat": city_lat, "lon": city_lon},
                airports=airports
            )

        except Exception as e:
            logger.error(f"Error finding nearest airports: {e}", exc_info=True)
            raise

        finally:
            if conn:
                self._postgres.release_connection(conn)

    def _find_best_city_match(
        self,
        conn,
        query: str
    ) -> Optional[Tuple[str, str, float, float, int]]:
        """
        Find best matching city using fuzzy matching.

        Returns:
            Tuple of (city_id, city_name, lat, lon, match_score) or None
        """
        cursor = conn.cursor()

        # Normalize query for better matching
        query_normalized = query.lower().strip()

        # Get all cities with their coordinates
        # Limit to reasonable candidates (cities with population data preferred)
        cursor.execute("""
            SELECT
                id,
                name,
                ST_Y(location::geometry) as lat,
                ST_X(location::geometry) as lon,
                population
            FROM public.cities
            WHERE
                location IS NOT NULL
                AND (
                    name ILIKE %s
                    OR name ILIKE %s
                )
            ORDER BY
                CASE
                    WHEN LOWER(name) = LOWER(%s) THEN 1
                    WHEN LOWER(name) LIKE LOWER(%s) THEN 2
                    ELSE 3
                END,
                population DESC NULLS LAST
            LIMIT 50
        """, (
            f"{query}%",  # Starts with
            f"%{query}%",  # Contains
            query,  # Exact match check
            f"{query}%"  # Starts with check
        ))

        candidates = cursor.fetchall()
        cursor.close()

        if not candidates:
            return None

        # Apply fuzzy matching to find best match
        best_match = None
        best_score = 0

        for city_id, city_name, lat, lon, population in candidates:
            # Calculate fuzzy match score
            score = fuzz.ratio(query_normalized, city_name.lower())

            # Bonus for exact match
            if query_normalized == city_name.lower():
                score = 100

            # Keep best match (minimum threshold: 80)
            if score > best_score and score >= 80:
                best_score = score
                best_match = (str(city_id), city_name, lat, lon, score)

        return best_match

    def _find_nearest_airports_to_location(
        self,
        conn,
        lat: float,
        lon: float,
        limit: int
    ) -> list[AirportResult]:
        """
        Find nearest airports to a geographic location using PostGIS.

        Args:
            conn: Database connection
            lat: Latitude
            lon: Longitude
            limit: Maximum number of airports

        Returns:
            List of AirportResult sorted by distance
        """
        cursor = conn.cursor()

        # Use PostGIS ST_Distance to calculate distances
        # ST_MakePoint creates a point, ST_Distance calculates distance
        # Convert to kilometers (PostGIS returns meters for geography type)
        query = """
            SELECT
                ref as iata,
                label as name,
                label as city_name,
                country_code,
                ST_Y(location::geometry) as lat,
                ST_X(location::geometry) as lon,
                ST_Distance(
                    location,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) / 1000.0 as distance_km
            FROM search_autocomplete
            WHERE
                type = 'airport'
                AND location IS NOT NULL
            ORDER BY distance_km ASC
            LIMIT %s
        """

        cursor.execute(query, (lon, lat, limit))
        rows = cursor.fetchall()
        cursor.close()

        airports = []
        for row in rows:
            iata, name, city_name, country_code, airport_lat, airport_lon, distance_km = row

            # Extract city name from airport label if needed
            # Format is usually "City Name (IATA)" or "Airport Name"
            if "(" in city_name:
                city_name = city_name.split("(")[0].strip()

            airports.append(
                AirportResult(
                    iata=iata,
                    name=name,
                    city_name=city_name,
                    country_code=country_code,
                    lat=airport_lat,
                    lon=airport_lon,
                    distance_km=round(distance_km, 2)
                )
            )

        logger.info(
            f"Found {len(airports)} airports near ({lat}, {lon}) "
            f"within range: {airports[0].distance_km:.2f}-{airports[-1].distance_km:.2f} km"
            if airports else f"Found 0 airports near ({lat}, {lon})"
        )

        return airports
