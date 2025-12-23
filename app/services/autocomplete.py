"""Autocomplete service for searching locations (countries, cities, airports)."""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from app.models.autocomplete import AutocompleteResult
from app.core.cache import cache_result

if TYPE_CHECKING:
    from app.db.postgres import PostgresManager

logger = logging.getLogger(__name__)


class AutocompleteService:
    """Service for location autocomplete search."""

    def __init__(self, postgres_manager: PostgresManager):
        self._postgres = postgres_manager

    @cache_result(ttl_seconds=600)  # Cache for 10 minutes
    def search(
        self,
        q: str,
        limit: int = 10,
        types: list[str] | None = None
    ) -> list[AutocompleteResult]:
        """
        Search locations matching the query.

        Args:
            q: Search query string
            limit: Maximum number of results (default: 10, max: 20)
            types: List of types to filter (default: all types)

        Returns:
            List of matching locations ordered by relevance (rank_signal DESC)
            Empty list if q < 3 characters

        The search uses the `search_autocomplete` view which combines:
        - Countries (type='country', id=iso2)
        - Cities (type='city', id=uuid)
        - Airports (type='airport', id=iata)

        Search strategy:
        1. Return empty if query < 3 chars
        2. Search in both label AND ref (airport codes like CDG, ORY)
        3. Priority ordering:
           - Exact code match (CDG, ORY) - HIGHEST PRIORITY
           - Exact label match (India)
           - Label starts with query (Ind...)
           - Label contains query (...india...)
        4. Within each priority level: airports > cities > countries
        5. Finally ordered by rank_signal (population for cities, fixed values for others)
        """

        # Return empty results if query too short
        search_term = q.strip()
        if len(search_term) < 3:
            logger.debug(f"Query too short (< 3 chars): '{search_term}'")
            return []

        conn = None
        try:
            conn = self._postgres.get_connection()
            cursor = conn.cursor()

            # Build WHERE clause for type filtering
            type_filter = ""
            query_params = []

            if types and len(types) > 0:
                # Filter by specified types
                placeholders = ",".join(["%s"] * len(types))
                type_filter = f"AND type IN ({placeholders})"
                query_params.extend(types)

            # Query optimisée avec recherche insensible à la casse
            # Extraction de lat/lon depuis le champ geography avec ST_Y et ST_X
            # Supporte aussi la recherche par code (ref) pour les aéroports (ex: CDG, ORY)
            query = f"""
                SELECT
                    type,
                    ref,
                    label,
                    country_code,
                    slug,
                    ST_Y(location::geometry) as lat,
                    ST_X(location::geometry) as lon,
                    rank_signal
                FROM search_autocomplete
                WHERE
                    (label ILIKE %s OR label ILIKE %s OR ref ILIKE %s)
                    {type_filter}
                ORDER BY
                    CASE
                        WHEN UPPER(ref) = UPPER(%s) THEN 0
                        WHEN LOWER(label) = LOWER(%s) THEN 1
                        WHEN LOWER(label) LIKE LOWER(%s) THEN 2
                        WHEN LOWER(label) LIKE LOWER(%s) THEN 3
                        ELSE 4
                    END,
                    CASE
                        WHEN type = 'airport' THEN 1
                        WHEN type = 'city' THEN 2
                        WHEN type = 'country' THEN 3
                    END,
                    rank_signal DESC,
                    label ASC
                LIMIT %s
            """

            starts_with = f"{search_term}%"
            contains = f"%{search_term}%"

            # Build complete parameter list
            params = [
                starts_with,  # WHERE label ILIKE %s (commence par)
                contains,     # OR label ILIKE %s (contient)
                search_term,  # OR ref ILIKE %s (code exact comme CDG)
                *query_params,  # Type filters if any
                search_term,  # ORDER BY CASE WHEN UPPER(ref) = UPPER(%s) (code exact - priorité absolue)
                search_term,  # ORDER BY CASE WHEN LOWER(label) = LOWER(%s) (label exact)
                starts_with,  # ORDER BY CASE WHEN... (priorité commence par)
                contains,     # ORDER BY CASE WHEN... (priorité contient)
                limit
            ]

            cursor.execute(query, params)

            results = []
            for row in cursor.fetchall():
                results.append(
                    AutocompleteResult(
                        type=row[0],
                        id=row[1],
                        label=row[2],
                        country_code=row[3],
                        slug=row[4],
                        lat=row[5],  # Can be None
                        lon=row[6]   # Can be None
                    )
                )

            cursor.close()
            logger.info(f"Autocomplete search for '{search_term}' (types={types}) returned {len(results)} results")

            return results

        except Exception as e:
            logger.error(f"Error during autocomplete search: {e}", exc_info=True)
            raise

        finally:
            if conn:
                self._postgres.release_connection(conn)
