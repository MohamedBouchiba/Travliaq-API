from __future__ import annotations
from typing import Any, Dict, Optional
import httpx
from datetime import datetime


class GooglePlacesClient:
    def __init__(self, api_key: str, http_client: httpx.AsyncClient, daily_cap: int = 9500):
        self.api_key = api_key
        self.http = httpx.AsyncClient() if http_client is None else http_client
        self.daily_cap = daily_cap
        self._request_count = 0

    def _guard_quota(self) -> None:
        if self._request_count >= self.daily_cap:
            raise RuntimeError("Google Places daily cap reached; refusing external calls")
        self._request_count += 1

    async def text_search(self, poi_name: str, city: str) -> Optional[Dict[str, Any]]:
        self._guard_quota()
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location",
        }
        payload = {"textQuery": f"{poi_name}, {city}", "languageCode": "en"}
        response = await self.http.post(url, headers=headers, json=payload, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        places = data.get("places", [])
        return places[0] if places else None

    async def place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        self._guard_quota()
        url = f"https://places.googleapis.com/v1/places/{place_id}"
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": ",".join(
                [
                    "id",
                    "displayName",
                    "formattedAddress",
                    "shortFormattedAddress",
                    "location",
                    "types",
                    "nationalPhoneNumber",
                    "internationalPhoneNumber",
                    "websiteUri",
                    "regularOpeningHours",
                ]
            ),
        }
        response = await self.http.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def normalize_basic(place: Dict[str, Any]) -> Dict[str, Any]:
        location = None
        if place.get("location"):
            location = {
                "lat": place["location"].get("latitude"),
                "lng": place["location"].get("longitude"),
            }
        phone = place.get("internationalPhoneNumber") or place.get("nationalPhoneNumber")
        regular_hours = place.get("regularOpeningHours")
        weekly = None
        if regular_hours and regular_hours.get("periods"):
            weekly = {}
            for period in regular_hours.get("periods", []):
                day = period.get("open", {}).get("day")
                open_time = period.get("open", {}).get("time")
                close_time = period.get("close", {}).get("time") if period.get("close") else None
                if day is not None and open_time:
                    # Format: "HHMM-HHMM" or just "HHMM" if no close time
                    time_range = "-".join(filter(None, [open_time, close_time])) if close_time else open_time
                    weekly.setdefault(str(day), []).append(time_range)
        return {
            "name": place.get("displayName", {}).get("text"),
            "formatted_address": place.get("formattedAddress"),
            "short_address": place.get("shortFormattedAddress"),
            "location": location,
            "phone": phone,
            "website": place.get("websiteUri"),
            "hours": {"weekly": weekly, "raw": regular_hours} if weekly or regular_hours else None,
            "types": place.get("types"),
        }

    @staticmethod
    def source_meta(fields: list[str]) -> Dict[str, Any]:
        return {"name": "google_places", "last_fetched": datetime.utcnow().isoformat(), "fields": fields}
