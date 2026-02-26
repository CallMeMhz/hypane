"""Storage model - independent JSON data container (MongoDB)."""

from dataclasses import dataclass, field
from datetime import datetime

from app import db


@dataclass
class Storage:
    id: str
    data: dict = field(default_factory=dict)
    user_id: str = "default"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    deleted_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def _to_doc(self) -> dict:
        """Convert to MongoDB document."""
        return {
            "_id": self.id,
            "user_id": self.user_id,
            "data": self.data,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
        }

    @classmethod
    def _from_doc(cls, doc: dict) -> "Storage":
        """Create from MongoDB document."""
        return cls(
            id=doc["_id"],
            data=doc.get("data", {}),
            user_id=doc.get("user_id", "default"),
            created_at=doc.get("created_at") or datetime.now(),
            updated_at=doc.get("updated_at") or datetime.now(),
            deleted_at=doc.get("deleted_at"),
        )

    async def save(self) -> None:
        """Save storage to MongoDB."""
        self.updated_at = datetime.now()
        await db.storages_col().update_one(
            {"_id": self.id},
            {"$set": self._to_doc()},
            upsert=True,
        )

    @classmethod
    async def load(cls, storage_id: str) -> "Storage | None":
        """Load storage from MongoDB."""
        doc = await db.storages_col().find_one({"_id": storage_id, "deleted_at": None})
        return cls._from_doc(doc) if doc else None

    @classmethod
    async def load_many(cls, storage_ids: list[str]) -> dict[str, "Storage"]:
        """Load multiple storages, returns {id: Storage}."""
        result = {}
        cursor = db.storages_col().find(
            {"_id": {"$in": storage_ids}, "deleted_at": None}
        )
        async for doc in cursor:
            s = cls._from_doc(doc)
            result[s.id] = s
        return result

    @classmethod
    async def list_all(cls, user_id: str = "default") -> list["Storage"]:
        """List all storages for a user."""
        cursor = db.storages_col().find({"user_id": user_id, "deleted_at": None})
        return [cls._from_doc(doc) async for doc in cursor]

    async def delete(self) -> bool:
        """Soft-delete storage."""
        result = await db.storages_col().update_one(
            {"_id": self.id, "deleted_at": None},
            {"$set": {"deleted_at": datetime.now()}},
        )
        return result.modified_count > 0
