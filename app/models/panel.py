"""Panel model - UI component with template and handler (MongoDB)."""

from dataclasses import dataclass, field
from datetime import datetime

from app import db


@dataclass
class Panel:
    id: str
    title: str = "Untitled"
    icon: str = "cube"
    headerColor: str = "gray"
    desc: str = ""
    size: str = "3x2"
    minSize: str = "2x2"
    storage_ids: list[str] = field(default_factory=list)
    facade: str = ""
    handler: str = ""
    user_id: str = "default"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    deleted_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "icon": self.icon,
            "headerColor": self.headerColor,
            "desc": self.desc,
            "size": self.size,
            "minSize": self.minSize,
            "storage_ids": self.storage_ids,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def _to_doc(self) -> dict:
        """Convert to MongoDB document."""
        return {
            "_id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "icon": self.icon,
            "headerColor": self.headerColor,
            "desc": self.desc,
            "size": self.size,
            "minSize": self.minSize,
            "storage_ids": self.storage_ids,
            "facade": self.facade,
            "handler": self.handler,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
        }

    @classmethod
    def _from_doc(cls, doc: dict) -> "Panel":
        """Create from MongoDB document."""
        return cls(
            id=doc["_id"],
            title=doc.get("title", "Untitled"),
            icon=doc.get("icon", "cube"),
            headerColor=doc.get("headerColor", "gray"),
            desc=doc.get("desc", ""),
            size=doc.get("size", "3x2"),
            minSize=doc.get("minSize", "2x2"),
            storage_ids=doc.get("storage_ids", []),
            facade=doc.get("facade", ""),
            handler=doc.get("handler", ""),
            user_id=doc.get("user_id", "default"),
            created_at=doc.get("created_at") or datetime.now(),
            updated_at=doc.get("updated_at") or datetime.now(),
            deleted_at=doc.get("deleted_at"),
        )

    async def save(self) -> None:
        """Save panel to MongoDB."""
        self.updated_at = datetime.now()
        await db.panels_col().update_one(
            {"_id": self.id},
            {"$set": self._to_doc()},
            upsert=True,
        )

    def get_template(self) -> str:
        """Get panel template HTML."""
        return self.facade

    async def set_template(self, html: str) -> None:
        """Set panel template HTML."""
        self.facade = html
        await self.save()

    def get_handler(self) -> str:
        """Get panel handler code."""
        return self.handler

    async def set_handler(self, code: str) -> None:
        """Set panel handler code."""
        self.handler = code
        await self.save()

    @classmethod
    async def load(cls, panel_id: str) -> "Panel | None":
        """Load panel from MongoDB."""
        doc = await db.panels_col().find_one({"_id": panel_id, "deleted_at": None})
        return cls._from_doc(doc) if doc else None

    @classmethod
    async def list_all(cls, user_id: str = "default") -> list["Panel"]:
        """List all panels for a user."""
        cursor = db.panels_col().find({"user_id": user_id, "deleted_at": None})
        return [cls._from_doc(doc) async for doc in cursor]

    async def delete(self) -> bool:
        """Soft-delete panel."""
        result = await db.panels_col().update_one(
            {"_id": self.id, "deleted_at": None},
            {"$set": {"deleted_at": datetime.now()}},
        )
        return result.modified_count > 0
