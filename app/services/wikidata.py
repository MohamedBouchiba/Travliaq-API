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


class WikidataClient:
    def __init__(self, user_agent: str, http_client: httpx.AsyncClient):
        self.user_agent = user_agent
        self.http = http_client or httpx.AsyncClient()

    async def fetch(self, poi_name: str, city: str) -> Optional[Dict[str, Any]]:
        query = SPARQL_TEMPLATE % f"{poi_name} ({city})"
        headers = {"Accept": "application/sparql-results+json", "User-Agent": self.user_agent}
        response = await self.http.get(
            "https://query.wikidata.org/sparql",
            params={"query": query},
            headers=headers,
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        bindings = data.get("results", {}).get("bindings", [])
        if not bindings:
            return None
        record = bindings[0]
        return self._normalize(record)

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
