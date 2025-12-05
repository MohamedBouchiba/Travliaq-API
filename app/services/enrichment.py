from __future__ import annotations
from datetime import datetime
from typing import Dict, Optional
from fastapi import HTTPException

from app.models.poi import (
    ContactInfo,
    FactsInfo,
    HoursInfo,
    POIDocument,
    POIRequest,
    PricingInfo,
)
from app.services.geoapify import GeoapifyClient
from app.services.google_places import GooglePlacesClient
from app.services.nominatim import NominatimClient
from app.services.poi_repository import POIRepository
from app.services.wikidata import WikidataClient
from app.utils.normalization import build_poi_key


class EnrichmentService:
    def __init__(
        self,
        repo: POIRepository,
        google: GooglePlacesClient,
        nominatim: NominatimClient,
        geoapify: GeoapifyClient,
        wikidata: WikidataClient,
        ttl_days: int,
        default_detail_types: list[str],
    ):
        self.repo = repo
        self.google = google
        self.nominatim = nominatim
        self.geoapify = geoapify
        self.wikidata = wikidata
        self.ttl_days = ttl_days
        self.default_detail_types = default_detail_types

    async def get_poi_details(self, payload: POIRequest) -> POIDocument:
        detail_types = payload.detail_types or self.default_detail_types
        detail_types = list(dict.fromkeys(detail_types))
        poi_key = build_poi_key(payload.poi_name, payload.city)

        existing = await self.repo.get_by_poi_key(poi_key)
        if existing and self.repo.is_fresh(existing) and self._has_required(existing, detail_types):
            return existing

        google_place = await self.google.text_search(payload.poi_name, payload.city)
        if not google_place and not existing:
            raise HTTPException(status_code=404, detail="POI not found in external providers or cache")

        place_id = google_place.get("id") if google_place else existing.place_id if existing else None
        existing_by_place = None
        if place_id:
            existing_by_place = await self.repo.get_by_place_id(place_id)
            if existing_by_place and self.repo.is_fresh(existing_by_place) and self._has_required(existing_by_place, detail_types):
                return existing_by_place

        google_details = None
        if place_id:
            google_details = await self.google.place_details(place_id)

        google_norm = GooglePlacesClient.normalize_basic(google_details or google_place or {}) if (google_details or google_place) else {}

        # 🆓 FREE GPS FALLBACK: Use Nominatim (OpenStreetMap) if Google didn't return coordinates
        location = google_norm.get("location")
        nominatim_norm = None
        if not location or not location.get("lat"):
            nominatim_norm = await self.nominatim.geocode(payload.poi_name, payload.city)
            if nominatim_norm and nominatim_norm.get("location"):
                location = nominatim_norm["location"]
                google_norm["location"] = location

        # 🌍 GEOAPIFY: Rich POI data (opening hours, contact, facilities)
        geoapify_norm = None
        if location and location.get("lat") and location.get("lng"):
            geoapify_norm = await self.geoapify.fetch_by_coords(
                lat=location["lat"], 
                lon=location["lng"],
                radius=100  # Tight radius for precise match
            )
        
        # Fallback: search by name if coords didn't return results
        if not geoapify_norm:
            geoapify_norm = await self.geoapify.fetch_by_name(
                name=payload.poi_name,
                city=payload.city
            )

        wikidata_norm = await self.wikidata.fetch(payload.poi_name, payload.city)

        base_doc = existing or existing_by_place
        merged = self._merge_documents(
            base_doc=base_doc,
            poi_key=poi_key,
            request_payload=payload,
            place_id=place_id,
            google_norm=google_norm,
            nominatim_norm=nominatim_norm,
            geoapify_norm=geoapify_norm,
            wikidata_norm=wikidata_norm,
            detail_types=detail_types,
        )
        merged.last_updated = datetime.utcnow()
        merged.ttl_days = self.ttl_days

        self._ensure_completeness(merged, detail_types)
        await self.repo.upsert(merged)
        return merged

    def _extract_country_from_address(self, formatted_address: str) -> Optional[str]:
        """Extract country from formatted address (usually last part)."""
        if not formatted_address:
            return None
        parts = [p.strip() for p in formatted_address.split(",")]
        if len(parts) >= 2:
            return parts[-1]
        return None

    def _merge_documents(
        self,
        base_doc: Optional[POIDocument],
        poi_key: str,
        request_payload: POIRequest,
        place_id: Optional[str],
        google_norm: Dict,
        nominatim_norm: Optional[Dict],
        geoapify_norm: Optional[Dict],
        wikidata_norm: Optional[Dict],
        detail_types: list[str],
    ) -> POIDocument:
        base_data = base_doc.model_dump() if base_doc else {}
        name = google_norm.get("name") or base_data.get("name") or request_payload.poi_name
        city = base_data.get("city") or request_payload.city
        
        # 🌍 COUNTRY EXTRACTION: Try multiple sources
        country = base_data.get("country")
        if not country and geoapify_norm:
            country = geoapify_norm.get("country")
        if not country and nominatim_norm:
            country = nominatim_norm.get("country")
        if not country and google_norm.get("formatted_address"):
            country = self._extract_country_from_address(google_norm.get("formatted_address"))

        location = google_norm.get("location") or base_data.get("location")
        
        # 📞 CONTACT: Merge from all sources
        contact = base_data.get("contact") or {}
        if google_norm.get("phone"):
            contact["phone"] = google_norm.get("phone")
        if google_norm.get("website"):
            contact["website"] = google_norm.get("website")
        if geoapify_norm:
            contact.setdefault("phone", geoapify_norm.get("phone"))
            contact.setdefault("website", geoapify_norm.get("website"))

        # ⏰ HOURS: Prefer Google, fallback to Geoapify
        hours = google_norm.get("hours")
        if not hours and geoapify_norm and geoapify_norm.get("hours"):
            hours = geoapify_norm.get("hours")
        if not hours:
            hours = base_data.get("hours")

        # 📚 FACTS: Merge from Wikidata + Geoapify
        facts = base_data.get("facts") or {}
        if wikidata_norm:
            facts.update({k: v for k, v in wikidata_norm.items() if v is not None})
        if geoapify_norm and geoapify_norm.get("description"):
            facts.setdefault("description", geoapify_norm.get("description"))
        if geoapify_norm and geoapify_norm.get("brand"):
            facts.setdefault("brand", geoapify_norm.get("brand"))
        if geoapify_norm and geoapify_norm.get("facilities"):
            facts.setdefault("facilities", geoapify_norm.get("facilities"))

        pricing = base_data.get("pricing") or None

        # 📊 SOURCES: Track what data came from where
        sources = base_data.get("sources") or {}
        if google_norm:
            sources["google_places"] = GooglePlacesClient.source_meta(list(google_norm.keys()))
        if geoapify_norm:
            sources["geoapify"] = GeoapifyClient.source_meta(list(geoapify_norm.keys()))
        if wikidata_norm:
            sources["wikidata"] = self.wikidata.source_meta(list(wikidata_norm.keys()))
        if nominatim_norm:
            sources["nominatim"] = NominatimClient.source_meta(list(nominatim_norm.keys()))

        document = POIDocument(
            poi_key=poi_key,
            name=name,
            city=city,
            country=country,
            location=location,
            place_id=place_id or base_data.get("place_id"),
            hours=hours,
            pricing=pricing,
            contact=contact,
            facts=facts,
            sources=sources,
            ttl_days=self.ttl_days,
            last_updated=datetime.utcnow(),
        )
        return document

    def _ensure_completeness(self, document: POIDocument, detail_types: list[str]) -> None:
        if "hours" in detail_types:
            if not document.hours:
                document.hours = HoursInfo(weekly=None, raw=None)
        if "pricing" in detail_types:
            if not document.pricing:
                document.pricing = PricingInfo()
        if "contact" in detail_types:
            if not document.contact:
                document.contact = ContactInfo()
            else:
                contact = ContactInfo(**document.contact) if isinstance(document.contact, dict) else document.contact
                document.contact = contact
        if "facts" in detail_types:
            if not document.facts:
                document.facts = FactsInfo()
            elif isinstance(document.facts, dict):
                document.facts = FactsInfo(**document.facts)

    def _has_required(self, doc: POIDocument, detail_types: list[str]) -> bool:
        for detail in detail_types:
            if detail == "hours":
                if not doc.hours or not (doc.hours.weekly or doc.hours.raw):
                    return False
            elif detail == "pricing":
                if not doc.pricing or not doc.pricing.admission_type:
                    return False
            elif detail == "contact":
                if not doc.contact or not (doc.contact.phone or doc.contact.website):
                    return False
            elif detail == "facts":
                facts_dict = doc.facts.model_dump() if hasattr(doc.facts, "model_dump") else doc.facts
                if not facts_dict or not any(v is not None for v in facts_dict.values()):
                    return False
        return True
