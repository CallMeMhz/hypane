"""Panel model - UI component with template and handler."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import json
from pathlib import Path

PANEL_DIR = Path("data/panels")


@dataclass
class Panel:
    id: str
    title: str = "Untitled"
    icon: str = "cube"
    headerColor: str = "gray"  # Header color name
    desc: str = ""  # Description for AI
    size: str = "3x2"
    minSize: str = "2x2"
    storage_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def dir(self) -> Path:
        return PANEL_DIR / self.id
    
    @property
    def metadata_path(self) -> Path:
        return self.dir / "metadata.json"
    
    @property
    def template_path(self) -> Path:
        return self.dir / "facade.html"
    
    @property
    def handler_path(self) -> Path:
        return self.dir / "handler.py"
    
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
    
    @classmethod
    def from_dict(cls, d: dict) -> "Panel":
        return cls(
            id=d["id"],
            title=d.get("title", "Untitled"),
            icon=d.get("icon", "cube"),
            headerColor=d.get("headerColor", "gray"),
            desc=d.get("desc", ""),
            size=d.get("size", "3x2"),
            minSize=d.get("minSize", "2x2"),
            storage_ids=d.get("storage_ids", []),
            created_at=datetime.fromisoformat(d["created_at"]) if "created_at" in d else datetime.now(),
            updated_at=datetime.fromisoformat(d["updated_at"]) if "updated_at" in d else datetime.now(),
        )
    
    def save(self) -> None:
        """Save panel metadata."""
        self.dir.mkdir(parents=True, exist_ok=True)
        self.updated_at = datetime.now()
        self.metadata_path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False))
    
    def get_template(self) -> str:
        """Get panel template HTML."""
        if self.template_path.exists():
            return self.template_path.read_text()
        return ""
    
    def set_template(self, html: str) -> None:
        """Set panel template HTML."""
        self.dir.mkdir(parents=True, exist_ok=True)
        self.template_path.write_text(html)
        self.updated_at = datetime.now()
        self.save()
    
    def get_handler(self) -> str:
        """Get panel handler code."""
        if self.handler_path.exists():
            return self.handler_path.read_text()
        return ""
    
    def set_handler(self, code: str) -> None:
        """Set panel handler code."""
        self.dir.mkdir(parents=True, exist_ok=True)
        self.handler_path.write_text(code)
        self.updated_at = datetime.now()
        self.save()
    
    @classmethod
    def load(cls, panel_id: str) -> "Panel | None":
        """Load panel from directory."""
        metadata_path = PANEL_DIR / panel_id / "metadata.json"
        if not metadata_path.exists():
            return None
        return cls.from_dict(json.loads(metadata_path.read_text()))
    
    @classmethod
    def list_all(cls) -> list["Panel"]:
        """List all panels."""
        PANEL_DIR.mkdir(parents=True, exist_ok=True)
        panels = []
        for path in PANEL_DIR.iterdir():
            if path.is_dir():
                panel = cls.load(path.name)
                if panel:
                    panels.append(panel)
        return panels
    
    def delete(self) -> bool:
        """Soft-delete panel directory (move to trash)."""
        import shutil
        if not self.dir.exists():
            return False
        trash = Path("data/_trash/panels") / self.id
        trash.parent.mkdir(parents=True, exist_ok=True)
        if trash.exists():
            shutil.rmtree(trash)
        shutil.move(str(self.dir), str(trash))
        return True
