"""
Geoapify Places API client - Rich POI data from OpenStreetMap.
Provides opening hours, contact info, facilities, and more.

Documentation: https://apidocs.geoapify.com/docs/places/
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import httpx
from datetime import datetime


class GeoapifyClient:
    """Geoapify Places API client for rich POI data."""
    
    PLACES_API_URL = "https://api.geoapify.com/v2/places"
    PLACE_DETAILS_API_URL = "https://api.geoapify.com/v2/place-details"
    GEOCODE_API_URL = "https://api.geoapify.com/v1/geocode/search"
    
    # Travel-relevant categories from Geoapify documentation
    TRAVEL_CATEGORIES = {
        # Tourism & Attractions
        "tourism": "tourism",
        "attraction": "tourism.attraction",
        "sights": "tourism.sights",
        "viewpoint": "tourism.attraction.viewpoint",
        "artwork": "tourism.attraction.artwork",
        "fountain": "tourism.attraction.fountain",
        
        # Culture & Entertainment  
        "museum": "entertainment.museum",
        "culture": "entertainment.culture",
        "theatre": "entertainment.culture.theatre",
        "gallery": "entertainment.culture.gallery",
        "cinema": "entertainment.cinema",
        "zoo": "entertainment.zoo",
        "aquarium": "entertainment.aquarium",
        "theme_park": "entertainment.theme_park",
        
        # Religious Sites
        "church": "tourism.sights.place_of_worship.church",
        "cathedral": "tourism.sights.place_of_worship.cathedral",
        "mosque": "tourism.sights.place_of_worship.mosque",
        "synagogue": "tourism.sights.place_of_worship.synagogue",
        "temple": "tourism.sights.place_of_worship.temple",
        
        # Historic
        "castle": "tourism.sights.castle",
        "monument": "tourism.sights.memorial.monument",
        "memorial": "tourism.sights.memorial",
        "ruins": "tourism.sights.ruines",
        "fort": "tourism.sights.fort",
        
        # Catering
        "restaurant": "catering.restaurant",
        "cafe": "catering.cafe",
        "bar": "catering.bar",
        "fast_food": "catering.fast_food",
        
        # Accommodation
        "hotel": "accommodation.hotel",
        "hostel": "accommodation.hostel",
        "guest_house": "accommodation.guest_house",
        
        # Practical
        "supermarket": "commercial.supermarket",
        "pharmacy": "healthcare.pharmacy",
        "atm": "service.financial.atm",
        "bank": "service.financial.bank",
        
        # Leisure
        "park": "leisure.park",
        "beach": "beach",
        "playground": "leisure.playground",
        
        # Heritage
        "heritage": "heritage",
        "unesco": "heritage.unesco",
    }
    
    def __init__(self, api_key: str, http_client: httpx.AsyncClient):
        self.api_key = api_key
        self.http = http_client or httpx.AsyncClient()
    
    async def fetch_by_coords(
        self, 
        lat: float, 
        lon: float, 
        radius: int = 100,
        categories: List[str] = None,
        name: str = None,
        lang: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch POI details by coordinates using Places API.
        
        Args:
            lat: Latitude
            lon: Longitude  
            radius: Search radius in meters (default 100m for precise match)
            categories: List of categories to filter (default: tourism + entertainment)
            name: Optional name filter for more precise matching
            lang: Language for results (default: en)
            
        Returns:
            Dict with normalized POI data or None
        """
        # Default to broad tourism/entertainment categories
        if not categories:
            categories = ["tourism", "entertainment", "heritage", "leisure.park"]
        
        params = {
            "categories": ",".join(categories),
            "filter": f"circle:{lon},{lat},{radius}",
            "limit": 1,
            "lang": lang,
            "apiKey": self.api_key,
        }
        
        # Add name filter for more precise matching
        if name:
            params["name"] = name
        
        return await self._call_places_api(params)
    
    async def fetch_by_name(
        self,
        name: str,
        city: str,
        country: str = None,
        lang: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Search POI by name and city using Geocoding API.
        Fallback when coordinates don't return results.
        
        Args:
            name: POI name (e.g., "Tour Eiffel")
            city: City name (e.g., "Paris")
            country: Optional country name
            lang: Language for results
            
        Returns:
            Dict with normalized POI data or None
        """
        query = f"{name}, {city}"
        if country:
            query += f", {country}"
        
        params = {
            "text": query,
            "type": "amenity",
            "limit": 1,
            "lang": lang,
            "apiKey": self.api_key,
        }
        
        return await self._call_geocode_api(params)
    
    async def fetch_place_details(
        self,
        place_id: str,
        features: List[str] = None,
        lang: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a place using Place Details API.
        
        Args:
            place_id: Geoapify place ID
            features: List of features to retrieve (default: details)
            lang: Language for results
            
        Returns:
            Dict with detailed POI data or None
        """
        if not features:
            features = ["details"]
        
        params = {
            "id": place_id,
            "features": ",".join(features),
            "lang": lang,
            "apiKey": self.api_key,
        }
        
        try:
            response = await self.http.get(
                self.PLACE_DETAILS_API_URL,
                params=params,
                headers={"Accept": "application/json"},
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            
            features_list = data.get("features", [])
            if features_list:
                return self._normalize_details(features_list[0])
        except Exception:
            pass
        
        return None
    
    async def _call_places_api(self, params: Dict) -> Optional[Dict[str, Any]]:
        """Call Places API and normalize response."""
        try:
            response = await self.http.get(
                self.PLACES_API_URL,
                params=params,
                headers={"Accept": "application/json"},
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            
            features = data.get("features", [])
            if features:
                return self._normalize_place(features[0])
        except Exception:
            pass
        
        return None
    
    async def _call_geocode_api(self, params: Dict) -> Optional[Dict[str, Any]]:
        """Call Geocoding API and normalize response."""
        try:
            response = await self.http.get(
                self.GEOCODE_API_URL,
                params=params,
                headers={"Accept": "application/json"},
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            
            features = data.get("features", [])
            if features:
                return self._normalize_geocode(features[0])
        except Exception:
            pass
        
        return None
    
    def _normalize_place(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Places API response to standard format."""
        props = feature.get("properties", {})
        datasource = props.get("datasource", {})
        raw = datasource.get("raw", {})
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [None, None])
        
        # Opening hours (from raw OSM data)
        opening_hours = props.get("opening_hours") or raw.get("opening_hours")
        hours = None
        if opening_hours:
            hours = {
                "weekly": None,  # String format like "Mo-Sa 07:00-20:00"
                "raw": opening_hours,
            }
        
        # Contact info
        contact = props.get("contact", {})
        phone = contact.get("phone") or raw.get("phone")
        website = props.get("website") or raw.get("website")
        email = contact.get("email") or raw.get("email")
        
        # Facilities
        facilities = props.get("facilities", {})
        
        # Payment options
        payment = props.get("payment_options", {})
        
        # Brand info
        brand = props.get("brand")
        brand_details = props.get("brand_details", {})
        
        # Categories
        categories = props.get("categories", [])
        
        return {
            "name": props.get("name"),
            "formatted_address": props.get("formatted"),
            "address_line1": props.get("address_line1"),
            "address_line2": props.get("address_line2"),
            "country": props.get("country"),
            "country_code": props.get("country_code"),
            "city": props.get("city"),
            "postcode": props.get("postcode"),
            "street": props.get("street"),
            "location": {
                "lat": coords[1] if len(coords) > 1 else None,
                "lng": coords[0] if len(coords) > 0 else None,
            },
            "phone": phone,
            "website": website,
            "email": email,
            "hours": hours,
            "categories": categories,
            "facilities": facilities,
            "payment_options": payment,
            "brand": brand,
            "brand_wikidata": brand_details.get("wikidata"),
            "brand_wikipedia": brand_details.get("wikipedia"),
            "description": raw.get("description"),
            "place_id": props.get("place_id"),
            "osm_id": raw.get("osm_id"),
            "osm_type": raw.get("osm_type"),
        }
    
    def _normalize_geocode(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Geocoding API response."""
        props = feature.get("properties", {})
        
        return {
            "name": props.get("name") or props.get("address_line1"),
            "formatted_address": props.get("formatted"),
            "country": props.get("country"),
            "country_code": props.get("country_code"),
            "city": props.get("city"),
            "location": {
                "lat": props.get("lat"),
                "lng": props.get("lon"),
            },
            "categories": props.get("categories", []),
            "place_id": props.get("place_id"),
        }
    
    def _normalize_details(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Place Details API response."""
        props = feature.get("properties", {})
        
        # Extract wiki references
        wiki = props.get("wiki_and_media", {})
        
        # Extract facilities
        facilities = props.get("facilities", {})
        
        # Extract contact
        contact = {
            "phone": props.get("contact", {}).get("phone"),
            "website": props.get("website"),
            "email": props.get("contact", {}).get("email"),
        }
        
        return {
            "name": props.get("name"),
            "formatted_address": props.get("formatted"),
            "country": props.get("country"),
            "city": props.get("city"),
            "location": {
                "lat": props.get("lat"),
                "lng": props.get("lon"),
            },
            "phone": contact.get("phone"),
            "website": contact.get("website"),
            "email": contact.get("email"),
            "hours": {"raw": props.get("opening_hours")} if props.get("opening_hours") else None,
            "facilities": facilities,
            "description": props.get("description"),
            "wikidata": wiki.get("wikidata"),
            "wikipedia": wiki.get("wikipedia"),
            "image": wiki.get("image"),
            "place_id": props.get("place_id"),
            "categories": props.get("categories", []),
        }
    
    @staticmethod
    def source_meta(fields: list[str]) -> Dict[str, Any]:
        return {
            "name": "geoapify",
            "last_fetched": datetime.utcnow().isoformat(),
            "fields": fields,
        }
