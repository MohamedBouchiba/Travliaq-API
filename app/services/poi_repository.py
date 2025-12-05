from datetime import datetime, timedelta
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.poi import POIDocument


class POIRepository:
    def __init__(self, collection: AsyncIOMotorCollection, ttl_days: int):
        self.collection = collection
        self.ttl_days = ttl_days

    async def get_by_poi_key(self, poi_key: str) -> Optional[POIDocument]:
        raw = await self.collection.find_one({"poi_key": poi_key})
        return POIDocument(**raw) if raw else None

    async def get_by_place_id(self, place_id: str) -> Optional[POIDocument]:
        raw = await self.collection.find_one({"place_id": place_id})
        return POIDocument(**raw) if raw else None

    async def upsert(self, document: POIDocument) -> POIDocument:
        payload = document.model_dump()
        await self.collection.update_one(
            {"poi_key": document.poi_key}, {"$set": payload}, upsert=True
        )
        return document

    def is_fresh(self, doc: POIDocument) -> bool:
        expiry = doc.last_updated + timedelta(days=doc.ttl_days)
        return datetime.utcnow() <= expiry
