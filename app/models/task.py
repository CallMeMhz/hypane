"""Task model - scheduled job with handler (MongoDB)."""

from dataclasses import dataclass, field
from datetime import datetime

from app import db


@dataclass
class Task:
    id: str
    name: str = "Untitled Task"
    schedule: str = ""
    storage_ids: list[str] = field(default_factory=list)
    enabled: bool = True
    handler: str = ""
    user_id: str = "default"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_run: datetime | None = None
    deleted_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "schedule": self.schedule,
            "storage_ids": self.storage_ids,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None,
        }

    def _to_doc(self) -> dict:
        """Convert to MongoDB document."""
        return {
            "_id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "schedule": self.schedule,
            "storage_ids": self.storage_ids,
            "enabled": self.enabled,
            "handler": self.handler,
            "last_run": self.last_run,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
        }

    @classmethod
    def _from_doc(cls, doc: dict) -> "Task":
        """Create from MongoDB document."""
        return cls(
            id=doc["_id"],
            name=doc.get("name", "Untitled Task"),
            schedule=doc.get("schedule", ""),
            storage_ids=doc.get("storage_ids", []),
            enabled=doc.get("enabled", True),
            handler=doc.get("handler", ""),
            user_id=doc.get("user_id", "default"),
            created_at=doc.get("created_at") or datetime.now(),
            updated_at=doc.get("updated_at") or datetime.now(),
            last_run=doc.get("last_run"),
            deleted_at=doc.get("deleted_at"),
        )

    async def save(self) -> None:
        """Save task to MongoDB."""
        self.updated_at = datetime.now()
        await db.tasks_col().update_one(
            {"_id": self.id},
            {"$set": self._to_doc()},
            upsert=True,
        )

    def get_handler(self) -> str:
        """Get task handler code."""
        return self.handler

    async def set_handler(self, code: str) -> None:
        """Set task handler code."""
        self.handler = code
        await self.save()

    @classmethod
    async def load(cls, task_id: str) -> "Task | None":
        """Load task from MongoDB."""
        doc = await db.tasks_col().find_one({"_id": task_id, "deleted_at": None})
        return cls._from_doc(doc) if doc else None

    @classmethod
    async def list_all(cls, user_id: str = "default") -> list["Task"]:
        """List all tasks for a user."""
        cursor = db.tasks_col().find({"user_id": user_id, "deleted_at": None})
        return [cls._from_doc(doc) async for doc in cursor]

    async def delete(self) -> bool:
        """Soft-delete task."""
        result = await db.tasks_col().update_one(
            {"_id": self.id, "deleted_at": None},
            {"$set": {"deleted_at": datetime.now()}},
        )
        return result.modified_count > 0
