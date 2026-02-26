"""MongoDB connection management via Motor."""

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect(uri: str, db_name: str = "hypane"):
    """Initialize MongoDB connection. Call during app startup."""
    if not uri:
        raise RuntimeError("MONGO_DSN environment variable is not set")
    global _client, _db
    _client = AsyncIOMotorClient(uri)
    _db = _client[db_name]
    await _ensure_indexes()
    logger.info("Connected to MongoDB: %s", db_name)


async def close():
    """Close MongoDB connection. Call during app shutdown."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    return _db


def panels_col():
    return _db["panels"]


def storages_col():
    return _db["storages"]


def tasks_col():
    return _db["tasks"]


def dashboards_col():
    return _db["dashboards"]


async def _ensure_indexes():
    for col_name in ["panels", "storages", "tasks"]:
        col = _db[col_name]
        await col.create_index([("user_id", 1), ("deleted_at", 1)])
    await _db["dashboards"].create_index([("user_id", 1)])
    logger.info("MongoDB indexes ensured")
