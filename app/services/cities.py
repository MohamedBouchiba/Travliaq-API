"""Service for city-related operations."""

import re
import logging
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
        """Convert text to slug format.

        Args:
            text: Text to slugify (e.g., "United States", "Côte d'Ivoire")

        Returns:
            Slugified text (e.g., "united-states", "cote-d-ivoire")
        """
        # Convert to lowercase
        text = text.lower().strip()
        # Remove accents/diacritics (simple approach)
        text = re.sub(r'[àáâãäå]', 'a', text)
        text = re.sub(r'[èéêë]', 'e', text)
        text = re.sub(r'[ìíîï]', 'i', text)
        text = re.sub(r'[òóôõö]', 'o', text)
        text = re.sub(r'[ùúûü]', 'u', text)
        text = re.sub(r'[ýÿ]', 'y', text)
        text = re.sub(r'[ñ]', 'n', text)
        text = re.sub(r'[ç]', 'c', text)
        # Replace spaces and non-alphanumeric with hyphens
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
            cursor.close()

            if result:
                country_code = result[0]
                logger.info(f"Resolved '{identifier}' → '{country_code}'")
                return country_code

            logger.warning(f"Could not resolve country identifier: '{identifier}' (slug: '{slug}')")
            return None

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

            # Use search_autocomplete view which already filters for real cities (not administrative divisions)
            # Get total count of cities from search_autocomplete
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM search_autocomplete
                WHERE type = 'city'
                    AND UPPER(country_code) = %s
                """,
                (country_code,)
            )
            total_cities = cursor.fetchone()[0]

            # If no cities found, return None
            if total_cities == 0:
                return None

            # Adjust limit based on country size
            # Small countries (<=10 cities): return max 1-2 cities
            # Larger countries: use requested limit
            if total_cities <= 10:
                effective_limit = min(2, total_cities)
            else:
                effective_limit = min(limit, total_cities)

            # Get top cities from search_autocomplete (which filters real cities)
            # Join with cities table to get full details including population
            query = """
                SELECT
                    c.id,
                    c.name,
                    c.country_code,
                    sa.slug,
                    c.population,
                    ST_Y(c.location::geometry) as lat,
                    ST_X(c.location::geometry) as lon
                FROM search_autocomplete sa
                INNER JOIN public.cities c ON c.id::text = sa.ref
                WHERE sa.type = 'city'
                    AND UPPER(sa.country_code) = %s
                ORDER BY
                    c.population DESC NULLS LAST,
                    c.name ASC
                LIMIT %s
            """

            cursor.execute(query, (country_code, effective_limit))
            rows = cursor.fetchall()

            cities = []
            for row in rows:
                city_id, name, cc, slug, population, lat, lon = row
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

            cursor.close()

            return TopCitiesResponse(
                country_code=country_code,
                total_cities=total_cities,
                cities=cities
            )

        finally:
            self.postgres_manager.release_connection(conn)
