"""Dashboard service - manages layout and panel arrangement."""

import json
from typing import Any

from app.config import DASHBOARD_FILE
from app.models.panel import Panel


def get_dashboard_layout() -> dict[str, Any]:
    """Get dashboard layout (panel positions and sizes)."""
    if not DASHBOARD_FILE.exists():
        return {"version": 2, "panels": []}
    
    with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data


def save_dashboard_layout(data: dict[str, Any]) -> None:
    """Save dashboard layout."""
    DASHBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
    data["version"] = 2
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_panel_layout(panel_id: str) -> dict | None:
    """Get layout info for a specific panel."""
    layout = get_dashboard_layout()
    for p in layout.get("panels", []):
        if p.get("id") == panel_id:
            return p
    return None


def update_panel_layout(panel_id: str, position: dict = None, size: str = None) -> bool:
    """Update panel position/size in layout."""
    layout = get_dashboard_layout()
    
    for p in layout.get("panels", []):
        if p.get("id") == panel_id:
            if position is not None:
                p["position"] = position
            if size is not None:
                p["size"] = size
            save_dashboard_layout(layout)
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
            # Check if all cells for the new panel are free
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

    # Fallback: place below everything
    return {"x": 0, "y": max_y}


def add_panel_to_layout(panel_id: str, position: dict = None, size: str = "3x2") -> None:
    """Add a panel to the layout."""
    layout = get_dashboard_layout()
    panels = layout.get("panels", [])
    
    # Assign order (append to end)
    max_order = max((p.get("order", 0) for p in panels), default=-1)
    
    # Default position: find first empty slot that fits the new panel
    if position is None:
        position = _find_first_empty_slot(panels, size)
    
    panels.append({
        "id": panel_id,
        "position": position,
        "size": size,
        "order": max_order + 1,
    })
    
    layout["panels"] = panels
    save_dashboard_layout(layout)


def remove_panel_from_layout(panel_id: str) -> bool:
    """Remove a panel from the layout."""
    layout = get_dashboard_layout()
    panels = layout.get("panels", [])
    original_len = len(panels)
    layout["panels"] = [p for p in panels if p.get("id") != panel_id]
    
    if len(layout["panels"]) < original_len:
        save_dashboard_layout(layout)
        return True
    return False


def update_panel_positions(updates: dict[str, dict]) -> None:
    """
    Batch update panel positions.
    
    Args:
        updates: {panel_id: {"x": int, "y": int}, ...}
    """
    layout = get_dashboard_layout()
    
    for p in layout.get("panels", []):
        panel_id = p.get("id")
        if panel_id in updates:
            pos = updates[panel_id]
            p["position"] = {"x": pos["x"], "y": pos["y"]}
    
    save_dashboard_layout(layout)


def get_dashboard(enrich: bool = True) -> dict[str, Any]:
    """
    Get full dashboard with panel data merged.
    This is what the frontend needs for rendering.
    """
    layout = get_dashboard_layout()
    
    # Build full panel list with data from Panel model
    panels = []
    for idx, panel_layout in enumerate(layout.get("panels", [])):
        panel_id = panel_layout.get("id")
        panel = Panel.load(panel_id)
        
        if panel:
            panel_dict = panel.to_dict()
            panel_dict.update({
                "position": panel_layout.get("position", {"x": 0, "y": 0}),
                "size": panel_layout.get("size", panel.size or "3x2"),
                "order": panel_layout.get("order", idx),
            })
            panels.append(panel_dict)
    
    # Sort by order
    panels.sort(key=lambda p: p.get("order", 0))
    
    return {
        "version": 2,
        "panels": panels,
        "userPreferences": layout.get("userPreferences", {}),
    }


def save_dashboard(data: dict[str, Any]) -> None:
    """Save full dashboard."""
    DASHBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
