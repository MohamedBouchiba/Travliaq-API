"""
Nominatim geocoding client (OpenStreetMap) - FREE, no API key required.
Used as fallback for GPS coordinates when Google Places is unavailable.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
import httpx
from datetime import datetime


class NominatimClient:
    """Free geocoding using OpenStreetMap's Nominatim API."""
    
    BASE_URL = "https://nominatim.openstreetmap.org"
    
    def __init__(self, user_agent: str, http_client: httpx.AsyncClient):
        self.user_agent = user_agent
        self.http = http_client or httpx.AsyncClient()
    
    async def geocode(self, poi_name: str, city: str) -> Optional[Dict[str, Any]]:
        """
        Geocode a POI name + city to get GPS coordinates.
        
        Args:
            poi_name: Name of the place (e.g., "Tour Eiffel")
            city: City name (e.g., "Paris")
            
        Returns:
            Dict with location info or None if not found
        """
        headers = {"User-Agent": self.user_agent}
        
        # Strategy 1: Search with POI name + city
        result = await self._search(f"{poi_name}, {city}", headers)
        if result:
            return result
        
        # Strategy 2: Try just POI name
        result = await self._search(poi_name, headers)
        return result
    
    async def _search(self, query: str, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Execute a search query on Nominatim."""
        try:
            response = await self.http.get(
                f"{self.BASE_URL}/search",
                params={
                    "q": query,
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1,
                },
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            results = response.json()
            
            if results and len(results) > 0:
                return self._normalize(results[0])
        except Exception:
            pass
        return None
    
    def _normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Nominatim response to standard format."""
        lat = data.get("lat")
        lon = data.get("lon")
        address = data.get("address", {})
        
        return {
            "location": {
                "lat": float(lat) if lat else None,
                "lng": float(lon) if lon else None,
            },
            "name": data.get("display_name", "").split(",")[0],
            "formatted_address": data.get("display_name"),
            "country": address.get("country"),
            "city": address.get("city") or address.get("town") or address.get("village"),
        }
    
    @staticmethod
    def source_meta(fields: list[str]) -> Dict[str, Any]:
        return {"name": "nominatim", "last_fetched": datetime.utcnow().isoformat(), "fields": fields}
