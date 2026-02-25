"""Task model - scheduled job with handler."""

from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

TASK_DIR = Path("data/tasks")


@dataclass
class Task:
    id: str
    name: str = "Untitled Task"
    schedule: str = ""  # Cron expression, empty = disabled
    storage_ids: list[str] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_run: datetime | None = None
    
    @property
    def dir(self) -> Path:
        return TASK_DIR / self.id
    
    @property
    def metadata_path(self) -> Path:
        return self.dir / "metadata.json"
    
    @property
    def handler_path(self) -> Path:
        return self.dir / "handler.py"
    
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
    
    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        return cls(
            id=d["id"],
            name=d.get("name", "Untitled Task"),
            schedule=d.get("schedule", ""),
            storage_ids=d.get("storage_ids", []),
            enabled=d.get("enabled", True),
            created_at=datetime.fromisoformat(d["created_at"]) if "created_at" in d else datetime.now(),
            updated_at=datetime.fromisoformat(d["updated_at"]) if "updated_at" in d else datetime.now(),
            last_run=datetime.fromisoformat(d["last_run"]) if d.get("last_run") else None,
        )
    
    def save(self) -> None:
        """Save task metadata."""
        self.dir.mkdir(parents=True, exist_ok=True)
        self.updated_at = datetime.now()
        self.metadata_path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False))
    
    def get_handler(self) -> str:
        """Get task handler code."""
        if self.handler_path.exists():
            return self.handler_path.read_text()
        return ""
    
    def set_handler(self, code: str) -> None:
        """Set task handler code."""
        self.dir.mkdir(parents=True, exist_ok=True)
        self.handler_path.write_text(code)
        self.updated_at = datetime.now()
        self.save()
    
    @classmethod
    def load(cls, task_id: str) -> "Task | None":
        """Load task from directory."""
        metadata_path = TASK_DIR / task_id / "metadata.json"
        if not metadata_path.exists():
            return None
        return cls.from_dict(json.loads(metadata_path.read_text()))
    
    @classmethod
    def list_all(cls) -> list["Task"]:
        """List all tasks."""
        TASK_DIR.mkdir(parents=True, exist_ok=True)
        tasks = []
        for path in TASK_DIR.iterdir():
            if path.is_dir():
                task = cls.load(path.name)
                if task:
                    tasks.append(task)
        return tasks
    
    def delete(self) -> bool:
        """Delete task directory."""
        import shutil
        if self.dir.exists():
            shutil.rmtree(self.dir)
            return True
        return False
