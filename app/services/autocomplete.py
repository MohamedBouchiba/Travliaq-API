"""Autocomplete service for searching locations (countries, cities, airports)."""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from app.models.autocomplete import AutocompleteRequest, AutocompleteResult

if TYPE_CHECKING:
    from app.db.postgres import PostgresManager

logger = logging.getLogger(__name__)


class AutocompleteService:
    """Service for location autocomplete search."""

    def __init__(self, postgres_manager: PostgresManager):
        self._postgres = postgres_manager

    def search(self, request: AutocompleteRequest) -> list[AutocompleteResult]:
        """
        Search locations matching the query.

        Args:
            request: Autocomplete request with query and limit

        Returns:
            List of matching locations ordered by relevance (rank_signal DESC)

        The search uses the `search_autocomplete` view which combines:
        - Countries (type='country', ref=iso2)
        - Cities (type='city', ref=uuid)
        - Airports (type='airport', ref=iata)

        Search strategy:
        1. Exact match on start of label (highest priority)
        2. Partial match anywhere in label
        3. Ordered by rank_signal (population for cities, fixed values for others)
        """

        conn = None
        try:
            conn = self._postgres.get_connection()
            cursor = conn.cursor()

            # Query optimisée avec recherche insensible à la casse
            # Priorité aux résultats qui commencent par la requête
            query = """
                SELECT
                    type,
                    ref,
                    label,
                    country_code,
                    slug
                FROM search_autocomplete
                WHERE
                    label ILIKE %s
                    OR label ILIKE %s
                ORDER BY
                    CASE
                        WHEN LOWER(label) LIKE LOWER(%s) THEN 1
                        WHEN LOWER(label) LIKE LOWER(%s) THEN 2
                        ELSE 3
                    END,
                    rank_signal DESC,
                    label ASC
                LIMIT %s
            """

            # Paramètres de recherche
            search_term = request.query.strip()
            starts_with = f"{search_term}%"
            contains = f"%{search_term}%"

            cursor.execute(
                query,
                (
                    starts_with,  # WHERE label ILIKE %s (commence par)
                    contains,     # OR label ILIKE %s (contient)
                    starts_with,  # ORDER BY CASE WHEN... (priorité commence par)
                    contains,     # ORDER BY CASE WHEN... (priorité contient)
                    request.limit
                )
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    AutocompleteResult(
                        type=row[0],
                        ref=row[1],
                        label=row[2],
                        country_code=row[3],
                        slug=row[4]
                    )
                )

            cursor.close()
            logger.info(f"Autocomplete search for '{search_term}' returned {len(results)} results")

            return results

        except Exception as e:
            logger.error(f"Error during autocomplete search: {e}", exc_info=True)
            raise

        finally:
            if conn:
                self._postgres.release_connection(conn)
