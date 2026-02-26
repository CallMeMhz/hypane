"""Dashboard service - manages layout and panel arrangement (MongoDB)."""

from datetime import datetime
from typing import Any

from app import db
from app.models.panel import Panel


async def get_dashboard_layout(dashboard_id: str = "default") -> dict[str, Any]:
    """Get dashboard layout (panel positions and sizes)."""
    doc = await db.dashboards_col().find_one({"_id": dashboard_id})
    if not doc:
        doc = {
            "_id": dashboard_id,
            "user_id": "default",
            "name": "Default",
            "version": 2,
            "panels": [],
            "userPreferences": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        await db.dashboards_col().insert_one(doc)
    return doc


async def save_dashboard_layout(data: dict[str, Any], dashboard_id: str = "default") -> None:
    """Save dashboard layout."""
    data["version"] = 2
    data["updated_at"] = datetime.now()
    await db.dashboards_col().update_one(
        {"_id": dashboard_id},
        {"$set": data},
        upsert=True,
    )


async def get_panel_layout(panel_id: str, dashboard_id: str = "default") -> dict | None:
    """Get layout info for a specific panel."""
    layout = await get_dashboard_layout(dashboard_id)
    for p in layout.get("panels", []):
        if p.get("id") == panel_id:
            return p
    return None


async def update_panel_layout(
    panel_id: str, position: dict = None, size: str = None, dashboard_id: str = "default"
) -> bool:
    """Update panel position/size in layout."""
    layout = await get_dashboard_layout(dashboard_id)

    for p in layout.get("panels", []):
        if p.get("id") == panel_id:
            if position is not None:
                p["position"] = position
            if size is not None:
                p["size"] = size
            await save_dashboard_layout(layout, dashboard_id)
            return True

    return False


def _parse_size(size_str: str) -> tuple[int, int]:
    """Parse 'WxH' string into (w, h) tuple."""
    if "x" in size_str:
        parts = size_str.split("x")
        return int(parts[0]), int(parts[1])
    return 3, 2


def _find_first_empty_slot(panels: list, size: str) -> dict:
    """Scan the 12-column grid row by row to find the first slot that fits."""
    cols = 12
    new_w, new_h = _parse_size(size)

    # Build a set of occupied cells
    occupied = set()
    max_y = 0
    for p in panels:
        pos = p.get("position", {})
        px, py = pos.get("x", 0), pos.get("y", 0)
        pw, ph = _parse_size(p.get("size", "3x2"))
        for r in range(py, py + ph):
            for c in range(px, px + pw):
                occupied.add((c, r))
        bottom = py + ph
        if bottom > max_y:
            max_y = bottom

    # Scan row by row, column by column
    for y in range(max_y + new_h + 1):
        for x in range(cols - new_w + 1):
            fits = True
            for r in range(y, y + new_h):
                for c in range(x, x + new_w):
                    if (c, r) in occupied:
                        fits = False
                        break
                if not fits:
                    break
            if fits:
                return {"x": x, "y": y}

    return {"x": 0, "y": max_y}


async def add_panel_to_layout(
    panel_id: str, position: dict = None, size: str = "3x2", dashboard_id: str = "default"
) -> None:
    """Add a panel to the layout."""
    layout = await get_dashboard_layout(dashboard_id)
    panels = layout.get("panels", [])

    max_order = max((p.get("order", 0) for p in panels), default=-1)

    if position is None:
        position = _find_first_empty_slot(panels, size)

    panels.append({
        "id": panel_id,
        "position": position,
        "size": size,
        "order": max_order + 1,
    })

    layout["panels"] = panels
    await save_dashboard_layout(layout, dashboard_id)


async def remove_panel_from_layout(panel_id: str, dashboard_id: str = "default") -> bool:
    """Remove a panel from the layout."""
    layout = await get_dashboard_layout(dashboard_id)
    panels = layout.get("panels", [])
    original_len = len(panels)
    layout["panels"] = [p for p in panels if p.get("id") != panel_id]

    if len(layout["panels"]) < original_len:
        await save_dashboard_layout(layout, dashboard_id)
        return True
    return False


async def update_panel_positions(
    updates: dict[str, dict], dashboard_id: str = "default"
) -> None:
    """Batch update panel positions and sizes."""
    layout = await get_dashboard_layout(dashboard_id)

    for p in layout.get("panels", []):
        panel_id = p.get("id")
        if panel_id in updates:
            u = updates[panel_id]
            p["position"] = {"x": u["x"], "y": u["y"]}
            if u.get("w") and u.get("h"):
                p["size"] = f"{u['w']}x{u['h']}"

    await save_dashboard_layout(layout, dashboard_id)


async def get_dashboard(enrich: bool = True, dashboard_id: str = "default") -> dict[str, Any]:
    """Get full dashboard with panel data merged."""
    layout = await get_dashboard_layout(dashboard_id)

    panels = []
    for idx, panel_layout in enumerate(layout.get("panels", [])):
        panel_id = panel_layout.get("id")
        panel = await Panel.load(panel_id)

        if panel:
            panel_dict = panel.to_dict()
            panel_dict.update({
                "position": panel_layout.get("position", {"x": 0, "y": 0}),
                "size": panel_layout.get("size", panel.size or "3x2"),
                "order": panel_layout.get("order", idx),
            })
            panels.append(panel_dict)

    panels.sort(key=lambda p: p.get("order", 0))

    return {
        "version": 2,
        "panels": panels,
        "userPreferences": layout.get("userPreferences", {}),
    }


async def save_dashboard(data: dict[str, Any], dashboard_id: str = "default") -> None:
    """Save full dashboard."""
    await save_dashboard_layout(data, dashboard_id)


async def list_dashboards(user_id: str = "default") -> list[dict]:
    """List all dashboards for a user."""
    cursor = db.dashboards_col().find({"user_id": user_id})
    return [
        {
            "id": doc["_id"],
            "name": doc.get("name", doc["_id"]),
            "panel_count": len(doc.get("panels", [])),
        }
        async for doc in cursor
    ]


async def create_dashboard(dashboard_id: str, name: str, user_id: str = "default") -> dict:
    """Create a new dashboard."""
    doc = {
        "_id": dashboard_id,
        "user_id": user_id,
        "name": name,
        "version": 2,
        "panels": [],
        "userPreferences": {},
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    await db.dashboards_col().insert_one(doc)
    return {"id": dashboard_id, "name": name}


async def rename_dashboard(dashboard_id: str, name: str) -> bool:
    """Rename a dashboard."""
    r = await db.dashboards_col().update_one(
        {"_id": dashboard_id}, {"$set": {"name": name, "updated_at": datetime.now()}}
    )
    return r.modified_count > 0


async def delete_dashboard(dashboard_id: str) -> bool:
    """Delete a dashboard (not the panels on it)."""
    if dashboard_id == "default":
        return False
    r = await db.dashboards_col().delete_one({"_id": dashboard_id})
    return r.deleted_count > 0


async def remove_panel_from_all_dashboards(panel_id: str) -> None:
    """Remove a panel from all dashboards (used when panel is deleted)."""
    await db.dashboards_col().update_many(
        {"panels.id": panel_id},
        {"$pull": {"panels": {"id": panel_id}}, "$set": {"updated_at": datetime.now()}},
    )
