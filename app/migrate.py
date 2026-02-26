"""One-time migration: file-based data → MongoDB."""

import json
import logging
from datetime import datetime

from app import config, db

logger = logging.getLogger(__name__)


async def migrate_files_to_mongo():
    """Detect legacy file data in data/ and import into MongoDB."""
    # Skip if already migrated (dashboards collection has data)
    if await db.dashboards_col().count_documents({}) > 0:
        return

    data_dir = config.DATA_DIR
    migrated_any = False

    # --- Storages ---
    storages_dir = data_dir / "storages"
    if storages_dir.exists():
        for json_file in storages_dir.glob("*.json"):
            try:
                raw = json.loads(json_file.read_text())
                doc = {
                    "_id": raw.get("id", json_file.stem),
                    "user_id": "default",
                    "data": raw.get("data", {}),
                    "created_at": (
                        datetime.fromisoformat(raw["created_at"])
                        if raw.get("created_at")
                        else datetime.now()
                    ),
                    "updated_at": (
                        datetime.fromisoformat(raw["updated_at"])
                        if raw.get("updated_at")
                        else datetime.now()
                    ),
                    "deleted_at": None,
                }
                await db.storages_col().insert_one(doc)
                migrated_any = True
            except Exception as e:
                logger.warning("Failed to migrate storage %s: %s", json_file.name, e)

    # --- Panels ---
    panels_dir = data_dir / "panels"
    if panels_dir.exists():
        for panel_dir in panels_dir.iterdir():
            if not panel_dir.is_dir():
                continue
            meta_path = panel_dir / "metadata.json"
            if not meta_path.exists():
                continue
            try:
                meta = json.loads(meta_path.read_text())
                facade_path = panel_dir / "facade.html"
                handler_path = panel_dir / "handler.py"

                doc = {
                    "_id": meta.get("id", panel_dir.name),
                    "user_id": "default",
                    "title": meta.get("title", "Untitled"),
                    "icon": meta.get("icon", "cube"),
                    "headerColor": meta.get("headerColor", "gray"),
                    "desc": meta.get("desc", ""),
                    "size": meta.get("size", "3x2"),
                    "minSize": meta.get("minSize", "2x2"),
                    "storage_ids": meta.get("storage_ids", []),
                    "facade": facade_path.read_text() if facade_path.exists() else "",
                    "handler": handler_path.read_text() if handler_path.exists() else "",
                    "created_at": (
                        datetime.fromisoformat(meta["created_at"])
                        if meta.get("created_at")
                        else datetime.now()
                    ),
                    "updated_at": (
                        datetime.fromisoformat(meta["updated_at"])
                        if meta.get("updated_at")
                        else datetime.now()
                    ),
                    "deleted_at": None,
                }
                await db.panels_col().insert_one(doc)
                migrated_any = True
            except Exception as e:
                logger.warning("Failed to migrate panel %s: %s", panel_dir.name, e)

    # --- Tasks ---
    tasks_dir = data_dir / "tasks"
    if tasks_dir.exists():
        for task_dir in tasks_dir.iterdir():
            if not task_dir.is_dir():
                continue
            meta_path = task_dir / "metadata.json"
            if not meta_path.exists():
                continue
            try:
                meta = json.loads(meta_path.read_text())
                handler_path = task_dir / "handler.py"

                doc = {
                    "_id": meta.get("id", task_dir.name),
                    "user_id": "default",
                    "name": meta.get("name", "Untitled Task"),
                    "schedule": meta.get("schedule", ""),
                    "storage_ids": meta.get("storage_ids", []),
                    "enabled": meta.get("enabled", True),
                    "handler": handler_path.read_text() if handler_path.exists() else "",
                    "last_run": (
                        datetime.fromisoformat(meta["last_run"])
                        if meta.get("last_run")
                        else None
                    ),
                    "created_at": (
                        datetime.fromisoformat(meta["created_at"])
                        if meta.get("created_at")
                        else datetime.now()
                    ),
                    "updated_at": (
                        datetime.fromisoformat(meta["updated_at"])
                        if meta.get("updated_at")
                        else datetime.now()
                    ),
                    "deleted_at": None,
                }
                await db.tasks_col().insert_one(doc)
                migrated_any = True
            except Exception as e:
                logger.warning("Failed to migrate task %s: %s", task_dir.name, e)

    # --- Dashboard layout ---
    dashboard_file = config.DASHBOARD_FILE
    if dashboard_file.exists():
        try:
            layout = json.loads(dashboard_file.read_text())
            doc = {
                "_id": "default",
                "user_id": "default",
                "name": "Default",
                "version": layout.get("version", 2),
                "panels": layout.get("panels", []),
                "userPreferences": layout.get("userPreferences", {}),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            await db.dashboards_col().insert_one(doc)
            migrated_any = True
        except Exception as e:
            logger.warning("Failed to migrate dashboard layout: %s", e)

    if migrated_any:
        logger.info("Migration complete: files -> MongoDB")
    else:
        logger.info("No file data to migrate")
