"""Service for city-related operations."""

import re
import logging
import unicodedata
from typing import Optional
from app.db.postgres import PostgresManager
from app.models.cities import TopCitiesResponse, CityInfo
from app.core.cache import cache_result

logger = logging.getLogger(__name__)


class CitiesService:
    """Service for retrieving city information."""

    def __init__(self, postgres_manager: PostgresManager):
        """Initialize the cities service.

        Args:
            postgres_manager: PostgreSQL connection manager
        """
        self.postgres_manager = postgres_manager

    def _slugify(self, text: str) -> str:
        """Convert text to slug format using Unicode normalization.

        This method handles ALL Unicode characters including:
        - European accents (à, é, ü, ñ, etc.)
        - Nordic characters (ø, å, æ)
        - Special characters (ß, œ, ł, etc.)
        - Asian, Arabic, Cyrillic scripts (transliterated or removed)

        Args:
            text: Text to slugify (e.g., "United States", "Côte d'Ivoire", "Ελλάδα")

        Returns:
            Slugified text (e.g., "united-states", "cote-d-ivoire", "ellada")

        Examples:
            >>> _slugify("Côte d'Ivoire")
            "cote-d-ivoire"
            >>> _slugify("São Tomé and Príncipe")
            "sao-tome-and-principe"
            >>> _slugify("Åland Islands")
            "aland-islands"
        """
        # Normalize Unicode characters (NFD = Canonical Decomposition)
        # This separates base characters from combining diacritical marks
        # Example: "é" (U+00E9) → "e" (U+0065) + "́" (U+0301)
        text = unicodedata.normalize('NFD', text)

        # Encode to ASCII, ignoring characters that can't be represented
        # This removes all diacritical marks and non-ASCII characters
        text = text.encode('ascii', 'ignore').decode('ascii')

        # Convert to lowercase
        text = text.lower().strip()

        # Replace spaces and non-alphanumeric characters with hyphens
        text = re.sub(r'[^a-z0-9]+', '-', text)

        # Remove leading/trailing hyphens
        text = text.strip('-')

        return text

    def _resolve_country_code(self, country_identifier: str) -> Optional[str]:
        """Resolve country identifier (code or name) to ISO2 country code.

        Args:
            country_identifier: ISO2 code (e.g., "FR") or country name (e.g., "France")

        Returns:
            ISO2 country code (uppercase) or None if not found
        """
        identifier = country_identifier.strip()

        # Check if it's already an ISO2 code (2 uppercase letters)
        if len(identifier) == 2 and identifier.isalpha():
            return identifier.upper()

        # Otherwise, treat as country name - convert to slug and search
        slug = self._slugify(identifier)
        logger.debug(f"Searching for country with slug: '{slug}' from identifier: '{identifier}'")

        conn = self.postgres_manager.get_connection()
        try:
            cursor = conn.cursor()
            try:
                # Search in search_autocomplete view for country by slug
                cursor.execute(
                    """
                    SELECT ref
                    FROM search_autocomplete
                    WHERE type = 'country'
                        AND slug = %s
                    LIMIT 1
                    """,
                    (slug,)
                )

                result = cursor.fetchone()

                if result:
                    country_code = result[0]
                    logger.info(f"Resolved '{identifier}' → '{country_code}'")
                    return country_code

                logger.warning(f"Could not resolve country identifier: '{identifier}' (slug: '{slug}')")
                return None

            finally:
                cursor.close()

        finally:
            self.postgres_manager.release_connection(conn)

    @cache_result(ttl_seconds=1800)  # Cache for 30 minutes
    def get_top_cities_by_country(
        self,
        country_identifier: str,
        limit: int = 5
    ) -> Optional[TopCitiesResponse]:
        """Get top cities by population for a given country.

        Args:
            country_identifier: ISO2 country code (e.g., "FR") or country name (e.g., "France", "United States")
            limit: Maximum number of cities to return

        Returns:
            TopCitiesResponse if country found, None otherwise

        Note:
            Uses the search_autocomplete view which filters for real cities only.
            This excludes administrative divisions like departments, districts, and regions.
            Cities are ordered by population (largest first).
        """
        # Resolve country identifier to ISO2 code
        country_code = self._resolve_country_code(country_identifier)
        if not country_code:
            logger.warning(f"Failed to resolve country: '{country_identifier}'")
            return None

        conn = self.postgres_manager.get_connection()

        try:
            cursor = conn.cursor()
            try:
                # Use search_autocomplete view which already filters for real cities (not administrative divisions)
                # Optimize: Use window function to get count and data in single query
                query = """
                    WITH ranked_cities AS (
                        SELECT
                            c.id,
                            c.name,
                            c.country_code,
                            sa.slug,
                            c.population,
                            ST_Y(c.location::geometry) as lat,
                            ST_X(c.location::geometry) as lon,
                            COUNT(*) OVER() as total_cities
                        FROM search_autocomplete sa
                        INNER JOIN public.cities c ON c.id::text = sa.ref
                        WHERE sa.type = 'city'
                            AND UPPER(sa.country_code) = %s
                            AND c.population IS NOT NULL
                    )
                    SELECT
                        id, name, country_code, slug, population, lat, lon, total_cities
                    FROM ranked_cities
                    ORDER BY
                        population DESC,
                        name ASC
                    LIMIT %s
                """

                # Initial query with max possible limit to get total_cities
                cursor.execute(query, (country_code, limit))
                rows = cursor.fetchall()

                # If no cities found, return None
                if not rows:
                    return None

                # Get total from first row (all rows have same total_cities value)
                total_cities = rows[0][7] if rows else 0

                # Adjust limit based on country size
                # Small countries (<=10 cities): return max 1-2 cities
                # Larger countries: use requested limit
                if total_cities <= 10:
                    effective_limit = min(2, total_cities)
                    # Re-query with adjusted limit if needed
                    if effective_limit < len(rows):
                        rows = rows[:effective_limit]

                cities = []
                for row in rows:
                    city_id, name, cc, slug, population, lat, lon, _ = row
                    cities.append(
                        CityInfo(
                            id=str(city_id),
                            name=name,
                            country_code=cc,
                            slug=slug,
                            population=population,
                            lat=lat,
                            lon=lon
                        )
                    )

                return TopCitiesResponse(
                    country_code=country_code,
                    total_cities=total_cities,
                    cities=cities
                )

            finally:
                cursor.close()

        finally:
            self.postgres_manager.release_connection(conn)
