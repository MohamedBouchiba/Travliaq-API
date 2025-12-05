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
from app.services.google_places import GooglePlacesClient
from app.services.opentripmap import OpenTripMapClient
from app.services.poi_repository import POIRepository
from app.services.wikidata import WikidataClient
from app.utils.normalization import build_poi_key


class EnrichmentService:
    def __init__(
        self,
        repo: POIRepository,
        google: GooglePlacesClient,
        otm: OpenTripMapClient,
        wikidata: WikidataClient,
        ttl_days: int,
        default_detail_types: list[str],
    ):
        self.repo = repo
        self.google = google
        self.otm = otm
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

        otm_norm = None
        if google_norm.get("location"):
            loc = google_norm["location"]
            otm_raw = await self.otm.fetch(lat=loc["lat"], lon=loc["lng"])
            if otm_raw:
                otm_norm = self.otm.normalize(otm_raw)

        wikidata_norm = await self.wikidata.fetch(payload.poi_name, payload.city)

        base_doc = existing or existing_by_place
        merged = self._merge_documents(
            base_doc=base_doc,
            poi_key=poi_key,
            request_payload=payload,
            place_id=place_id,
            google_norm=google_norm,
            otm_norm=otm_norm,
            wikidata_norm=wikidata_norm,
            detail_types=detail_types,
        )
        merged.last_updated = datetime.utcnow()
        merged.ttl_days = self.ttl_days

        self._ensure_completeness(merged, detail_types)
        await self.repo.upsert(merged)
        return merged

    def _merge_documents(
        self,
        base_doc: Optional[POIDocument],
        poi_key: str,
        request_payload: POIRequest,
        place_id: Optional[str],
        google_norm: Dict,
        otm_norm: Optional[Dict],
        wikidata_norm: Optional[Dict],
        detail_types: list[str],
    ) -> POIDocument:
        base_data = base_doc.model_dump() if base_doc else {}
        name = google_norm.get("name") or base_data.get("name") or request_payload.poi_name
        city = base_data.get("city") or request_payload.city
        country = base_data.get("country")

        location = google_norm.get("location") or base_data.get("location")
        contact = base_data.get("contact") or {}
        if google_norm.get("phone"):
            contact["phone"] = google_norm.get("phone")
        if google_norm.get("website"):
            contact["website"] = google_norm.get("website")
        if otm_norm:
            contact.setdefault("phone", otm_norm.get("phone"))
            contact.setdefault("website", otm_norm.get("website"))

        hours = google_norm.get("hours") or (otm_norm.get("hours") if otm_norm else None) or base_data.get("hours")

        facts = base_data.get("facts") or {}
        if wikidata_norm:
            facts.update({k: v for k, v in wikidata_norm.items() if v is not None})
        if otm_norm and otm_norm.get("description"):
            facts.setdefault("description", otm_norm.get("description"))

        pricing = base_data.get("pricing") or None

        sources = base_data.get("sources") or {}
        if google_norm:
            sources["google_places"] = GooglePlacesClient.source_meta(list(google_norm.keys()))
        if otm_norm:
            sources["opentripmap"] = self.otm.source_meta(list(otm_norm.keys()))
        if wikidata_norm:
            sources["wikidata"] = self.wikidata.source_meta(list(wikidata_norm.keys()))

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
