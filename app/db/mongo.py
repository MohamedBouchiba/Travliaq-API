from __future__ import annotations
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import ASCENDING
from app.core.config import Settings


class MongoManager:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: AsyncIOMotorClient | None = None

    @property
    def client(self) -> AsyncIOMotorClient:
        if self._client is None:
            self._client = AsyncIOMotorClient(self._settings.mongodb_uri)
        return self._client

    def collection(self) -> AsyncIOMotorCollection:
        db = self.client[self._settings.mongodb_db]
        return db[self._settings.mongodb_collection_poi]

    async def init_indexes(self) -> None:
        collection = self.collection()
        await collection.create_index([("poi_key", ASCENDING)], unique=True)
        
        # Drop old unique index if exists, then create non-unique one
        try:
            await collection.drop_index("place_id_1")
        except Exception:
            pass  # Index doesn't exist
        
        await collection.create_index([("place_id", ASCENDING)], name="place_id_1", sparse=True)

    async def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
