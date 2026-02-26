"""Storage model - independent JSON data container."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import json
from pathlib import Path

STORAGE_DIR = Path("data/storages")


@dataclass
class Storage:
    id: str
    data: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> "Storage":
        return cls(
            id=d["id"],
            data=d.get("data", {}),
            created_at=datetime.fromisoformat(d["created_at"]) if "created_at" in d else datetime.now(),
            updated_at=datetime.fromisoformat(d["updated_at"]) if "updated_at" in d else datetime.now(),
        )
    
    def save(self) -> None:
        """Save storage to file."""
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.updated_at = datetime.now()
        path = STORAGE_DIR / f"{self.id}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False))
    
    @classmethod
    def load(cls, storage_id: str) -> "Storage | None":
        """Load storage from file."""
        path = STORAGE_DIR / f"{storage_id}.json"
        if not path.exists():
            return None
        return cls.from_dict(json.loads(path.read_text()))
    
    @classmethod
    def load_many(cls, storage_ids: list[str]) -> dict[str, "Storage"]:
        """Load multiple storages, returns {id: Storage}."""
        result = {}
        for sid in storage_ids:
            s = cls.load(sid)
            if s:
                result[sid] = s
        return result
    
    @classmethod
    def list_all(cls) -> list["Storage"]:
        """List all storages."""
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        storages = []
        for path in STORAGE_DIR.glob("*.json"):
            try:
                storages.append(cls.from_dict(json.loads(path.read_text())))
            except Exception:
                pass
        return storages
    
    def delete(self) -> bool:
        """Soft-delete storage file (move to trash)."""
        import shutil
        path = STORAGE_DIR / f"{self.id}.json"
        if not path.exists():
            return False
        trash = Path("data/_trash/storages")
        trash.mkdir(parents=True, exist_ok=True)
        dest = trash / f"{self.id}.json"
        if dest.exists():
            dest.unlink()
        shutil.move(str(path), str(dest))
        return True
