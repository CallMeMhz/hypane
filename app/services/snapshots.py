"""Dashboard snapshot service for version history."""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.config import DATA_DIR

SNAPSHOTS_DIR = DATA_DIR / "snapshots"
CHANGELOG_FILE = DATA_DIR / "changelog.json"


def _ensure_dirs():
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def _get_content_hash(data: dict) -> str:
    """Generate a short hash of dashboard content."""
    content = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(content.encode()).hexdigest()[:8]


def _load_changelog() -> list[dict]:
    """Load changelog entries."""
    if not CHANGELOG_FILE.exists():
        return []
    with open(CHANGELOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_changelog(entries: list[dict]):
    """Save changelog entries."""
    with open(CHANGELOG_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def create_snapshot(
    dashboard: dict,
    action: str,
    details: Optional[str] = None,
    panel_id: Optional[str] = None,
) -> dict:
    """
    Create a snapshot of the current dashboard state.
    
    Args:
        dashboard: Current dashboard data
        action: What was done (create, update, delete, merge)
        details: Human-readable description
        panel_id: Related panel ID if applicable
    
    Returns:
        The changelog entry
    """
    _ensure_dirs()
    
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    content_hash = _get_content_hash(dashboard)
    snapshot_id = f"{timestamp}_{content_hash}"
    
    # Save snapshot
    snapshot_file = SNAPSHOTS_DIR / f"{snapshot_id}.json"
    with open(snapshot_file, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)
    
    # Create changelog entry
    entry = {
        "id": snapshot_id,
        "timestamp": now.isoformat().replace("+00:00", "Z"),
        "action": action,
        "details": details,
        "panelId": panel_id,
        "panelCount": len(dashboard.get("panels", [])),
    }
    
    # Append to changelog
    changelog = _load_changelog()
    changelog.insert(0, entry)  # Newest first
    _save_changelog(changelog)
    
    return entry


def get_changelog(limit: int = 20) -> list[dict]:
    """Get recent changelog entries."""
    changelog = _load_changelog()
    return changelog[:limit]


def get_snapshot(snapshot_id: str) -> Optional[dict]:
    """Get a specific snapshot by ID."""
    snapshot_file = SNAPSHOTS_DIR / f"{snapshot_id}.json"
    if not snapshot_file.exists():
        return None
    with open(snapshot_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_snapshot_diff(snapshot_id: str, current_dashboard: dict) -> dict:
    """Compare a snapshot with current state."""
    snapshot = get_snapshot(snapshot_id)
    if not snapshot:
        return {"error": "Snapshot not found"}
    
    old_panels = {p["id"]: p for p in snapshot.get("panels", [])}
    new_panels = {p["id"]: p for p in current_dashboard.get("panels", [])}
    
    added = [p for pid, p in new_panels.items() if pid not in old_panels]
    removed = [p for pid, p in old_panels.items() if pid not in new_panels]
    
    modified = []
    for pid, new_panel in new_panels.items():
        if pid in old_panels:
            old_panel = old_panels[pid]
            if json.dumps(old_panel, sort_keys=True) != json.dumps(new_panel, sort_keys=True):
                modified.append({
                    "id": pid,
                    "title": new_panel.get("title"),
                    "changes": _get_panel_changes(old_panel, new_panel)
                })
    
    return {
        "snapshotId": snapshot_id,
        "added": [{"id": p["id"], "title": p.get("title")} for p in added],
        "removed": [{"id": p["id"], "title": p.get("title")} for p in removed],
        "modified": modified,
    }


def _get_panel_changes(old: dict, new: dict) -> list[str]:
    """Get list of changed fields between two panels."""
    changes = []
    for key in set(old.keys()) | set(new.keys()):
        if key in ("updatedAt",):
            continue
        old_val = old.get(key)
        new_val = new.get(key)
        if old_val != new_val:
            changes.append(key)
    return changes
