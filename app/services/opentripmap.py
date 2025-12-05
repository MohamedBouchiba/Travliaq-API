from __future__ import annotations
from typing import Any, Dict, Optional
import httpx
from datetime import datetime


class OpenTripMapClient:
    def __init__(self, api_key: str, http_client: httpx.AsyncClient, daily_cap: int = 9500):
        self.api_key = api_key
        self.http = httpx.AsyncClient() if http_client is None else http_client
        self.daily_cap = daily_cap
        self._request_count = 0

    def _guard_quota(self) -> None:
        if self._request_count >= self.daily_cap:
            raise RuntimeError("OpenTripMap daily cap reached; refusing external calls")
        self._request_count += 1

    async def fetch(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Find the closest object by coordinates then fetch details."""
        # Try with increasing radius if no results found
        for radius in [200, 500, 1000]:
            try:
                self._guard_quota()
                base_params = {"lon": lon, "lat": lat, "radius": radius, "limit": 1, "apikey": self.api_key, "format": "json"}
                radius_url = "https://api.opentripmap.com/0.1/en/places/radius"
                radius_resp = await self.http.get(radius_url, params=base_params, timeout=10.0)
                radius_resp.raise_for_status()
                results = radius_resp.json()
                
                if results and len(results) > 0:
                    xid = results[0].get("xid")
                    if xid:
                        self._guard_quota()
                        detail_url = f"https://api.opentripmap.com/0.1/en/places/xid/{xid}"
                        detail_resp = await self.http.get(detail_url, params={"apikey": self.api_key}, timeout=10.0)
                        detail_resp.raise_for_status()
                        return detail_resp.json()
            except Exception:
                continue
        return None

    @staticmethod
    def normalize(data: Dict[str, Any]) -> Dict[str, Any]:
        info = data.get("info", {})
        contacts = data.get("contacts", {})
        sources = data.get("sources", {})
        hours = data.get("opening_hours")
        phone = contacts.get("phone") if isinstance(contacts, dict) else None
        website = contacts.get("website") if isinstance(contacts, dict) else None

        weekly = None
        if isinstance(hours, dict) and hours.get("weekday_text"):
            weekly = {str(idx): [text] for idx, text in enumerate(hours.get("weekday_text", []))}

        return {
            "description": info.get("descr"),
            "phone": phone,
            "website": website,
            "hours": {"weekly": weekly, "raw": hours} if hours else None,
            "wikipedia_extracts": data.get("wikipedia_extracts", {}),
            "otm_link": sources.get("otm"),
        }

    @staticmethod
    def source_meta(fields: list[str]) -> Dict[str, Any]:
        return {"name": "opentripmap", "last_fetched": datetime.utcnow().isoformat(), "fields": fields}
