from __future__ import annotations
from typing import Any, Dict, Optional
import httpx
from datetime import datetime


# Query with proper description extraction
SPARQL_TEMPLATE = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX bd: <http://www.bigdata.com/rdf#>
PREFIX wikibase: <http://wikiba.se/ontology#>

SELECT ?item ?itemLabel ?itemDescription ?inception ?heritageLabel ?instanceLabel WHERE {
  ?item rdfs:label "%s"@en.
  OPTIONAL { ?item schema:description ?itemDescription. FILTER(LANG(?itemDescription) = "en") }
  OPTIONAL { ?item wdt:P571 ?inception. }
  OPTIONAL { ?item wdt:P1435 ?heritage. }
  OPTIONAL { ?item wdt:P31 ?instance. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 1
"""

# French label query (for French POI names)
SPARQL_TEMPLATE_FR = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX bd: <http://www.bigdata.com/rdf#>
PREFIX wikibase: <http://wikiba.se/ontology#>

SELECT ?item ?itemLabel ?itemDescription ?inception ?heritageLabel ?instanceLabel WHERE {
  ?item rdfs:label "%s"@fr.
  OPTIONAL { ?item schema:description ?itemDescription. FILTER(LANG(?itemDescription) = "en") }
  OPTIONAL { ?item wdt:P571 ?inception. }
  OPTIONAL { ?item wdt:P1435 ?heritage. }
  OPTIONAL { ?item wdt:P31 ?instance. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,fr". }
}
LIMIT 1
"""

# Fuzzy search with CONTAINS
SPARQL_TEMPLATE_FUZZY = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX bd: <http://www.bigdata.com/rdf#>
PREFIX wikibase: <http://wikiba.se/ontology#>

SELECT ?item ?itemLabel ?itemDescription ?inception ?heritageLabel ?instanceLabel WHERE {
  ?item rdfs:label ?label.
  FILTER(LANG(?label) = "en" && CONTAINS(LCASE(?label), LCASE("%s")))
  OPTIONAL { ?item schema:description ?itemDescription. FILTER(LANG(?itemDescription) = "en") }
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
        
        # Strategy 1: Exact match on POI name (English)
        result = await self._try_query(SPARQL_TEMPLATE % poi_name, headers)
        if result and result.get("description"):
            return result
        
        # Strategy 2: Try French label (for French POI names like "Tour Eiffel")
        result_fr = await self._try_query(SPARQL_TEMPLATE_FR % poi_name, headers)
        if result_fr and result_fr.get("description"):
            return result_fr
        
        # Strategy 3: Try with city in parentheses
        result = await self._try_query(SPARQL_TEMPLATE % f"{poi_name} ({city})", headers)
        if result and result.get("description"):
            return result
        
        # Strategy 4: Fuzzy search with CONTAINS
        result = await self._try_query(SPARQL_TEMPLATE_FUZZY % poi_name, headers)
        if result:
            return result
        
        # Return best result we found even without description
        return result_fr or result

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
        
        # Get real description from schema:description, not just the label
        description = binding.get("itemDescription", {}).get("value")
        label = binding.get("itemLabel", {}).get("value")
        
        # If no description, don't use the label as description (it's not helpful)
        if not description or description == label:
            description = None
        
        return {
            "year_built": year_built,
            "unesco_site": bool(binding.get("heritageLabel")),
            "instance_of": binding.get("instanceLabel", {}).get("value"),
            "description": description,
        }

    @staticmethod
    def source_meta(fields: list[str]) -> Dict[str, Any]:
        return {"name": "wikidata", "last_fetched": datetime.utcnow().isoformat(), "fields": fields}
