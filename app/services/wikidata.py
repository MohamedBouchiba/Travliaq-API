from __future__ import annotations
from typing import Any, Dict, Optional
import httpx
from datetime import datetime


SPARQL_TEMPLATE = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX bd: <http://www.bigdata.com/rdf#>
PREFIX wikibase: <http://wikiba.se/ontology#>

SELECT ?item ?itemLabel ?inception ?heritageLabel ?instanceLabel WHERE {
  ?item rdfs:label "%s"@en.
  OPTIONAL { ?item wdt:P571 ?inception. }
  OPTIONAL { ?item wdt:P1435 ?heritage. }
  OPTIONAL { ?item wdt:P31 ?instance. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 1
"""

# Alternative query using contains for fuzzy matching
SPARQL_TEMPLATE_FUZZY = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX bd: <http://www.bigdata.com/rdf#>
PREFIX wikibase: <http://wikiba.se/ontology#>

SELECT ?item ?itemLabel ?inception ?heritageLabel ?instanceLabel WHERE {
  ?item rdfs:label ?label.
  FILTER(LANG(?label) = "en" && CONTAINS(LCASE(?label), LCASE("%s")))
  OPTIONAL { ?item wdt:P571 ?inception. }
  OPTIONAL { ?item wdt:P1435 ?heritage. }
  OPTIONAL { ?item wdt:P31 ?instance. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 1
"""


class WikidataClient:
    def __init__(self, user_agent: str, http_client: httpx.AsyncClient):
        self.user_agent = user_agent
        self.http = http_client or httpx.AsyncClient()

    async def fetch(self, poi_name: str, city: str) -> Optional[Dict[str, Any]]:
        headers = {"Accept": "application/sparql-results+json", "User-Agent": self.user_agent}
        
        # Strategy 1: Exact match on POI name only (most common case)
        result = await self._try_query(SPARQL_TEMPLATE % poi_name, headers)
        if result:
            return result
        
        # Strategy 2: Try with city in parentheses (e.g., "Louvre Museum (Paris)")
        result = await self._try_query(SPARQL_TEMPLATE % f"{poi_name} ({city})", headers)
        if result:
            return result
        
        # Strategy 3: Fuzzy search with CONTAINS
        result = await self._try_query(SPARQL_TEMPLATE_FUZZY % poi_name, headers)
        return result

    async def _try_query(self, query: str, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        try:
            response = await self.http.get(
                "https://query.wikidata.org/sparql",
                params={"query": query},
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            bindings = data.get("results", {}).get("bindings", [])
            if bindings:
                return self._normalize(bindings[0])
        except Exception:
            pass
        return None

    def _normalize(self, binding: Dict[str, Any]) -> Dict[str, Any]:
        inception = binding.get("inception", {}).get("value")
        year_built = None
        if inception:
            try:
                year_built = int(inception.split("-")[0])
            except ValueError:
                year_built = None
        return {
            "year_built": year_built,
            "unesco_site": bool(binding.get("heritageLabel")),
            "instance_of": binding.get("instanceLabel", {}).get("value"),
            "description": binding.get("itemLabel", {}).get("value"),
        }

    @staticmethod
    def source_meta(fields: list[str]) -> Dict[str, Any]:
        return {"name": "wikidata", "last_fetched": datetime.utcnow().isoformat(), "fields": fields}
