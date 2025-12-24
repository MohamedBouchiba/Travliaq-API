"""Service for city-related operations."""

from typing import Optional
from app.db.postgres import PostgresManager
from app.models.cities import TopCitiesResponse, CityInfo
from app.core.cache import cache_result


class CitiesService:
    """Service for retrieving city information."""

    def __init__(self, postgres_manager: PostgresManager):
        """Initialize the cities service.

        Args:
            postgres_manager: PostgreSQL connection manager
        """
        self.postgres_manager = postgres_manager

    @cache_result(ttl_seconds=1800)  # Cache for 30 minutes
    def get_top_cities_by_country(
        self,
        country_code: str,
        limit: int = 5
    ) -> Optional[TopCitiesResponse]:
        """Get top cities by population for a given country.

        Args:
            country_code: ISO2 country code (e.g., "FR", "US")
            limit: Maximum number of cities to return

        Returns:
            TopCitiesResponse if country found, None otherwise
        """
        conn = self.postgres_manager.get_connection()

        try:
            cursor = conn.cursor()

            # Normalize country code (uppercase)
            country_code = country_code.upper().strip()

            # Get total count of cities in country
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM public.cities
                WHERE UPPER(country_code) = %s
                """,
                (country_code,)
            )
            total_cities = cursor.fetchone()[0]

            # If no cities found, return None
            if total_cities == 0:
                return None

            # Get top cities ordered by population
            query = """
                SELECT
                    id,
                    name,
                    country_code,
                    slug,
                    population,
                    ST_Y(location::geometry) as lat,
                    ST_X(location::geometry) as lon
                FROM public.cities
                WHERE UPPER(country_code) = %s
                ORDER BY
                    population DESC NULLS LAST,
                    name ASC
                LIMIT %s
            """

            cursor.execute(query, (country_code, limit))
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
