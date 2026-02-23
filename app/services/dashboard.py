"""Dashboard service - manages layout and panel arrangement."""

import json
from typing import Any

from app.config import DASHBOARD_FILE
from app.services.panels import get_panel, get_panel_data, list_panels


def get_dashboard_layout() -> dict[str, Any]:
    """
    Get dashboard layout (panel positions and sizes).
    """
    if not DASHBOARD_FILE.exists():
        return {"version": 2, "panels": []}
    
    with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle legacy format (version 1 with 'cards')
    if data.get("version", 1) == 1 and "cards" in data:
        return data  # Will be migrated separately
    
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


def add_panel_to_layout(panel_id: str, position: dict = None, size: str = "3x2") -> None:
    """Add a panel to the layout."""
    layout = get_dashboard_layout()
    
    # Default position: find next available spot
    if position is None:
        max_y = 0
        for p in layout.get("panels", []):
            pos = p.get("position", {})
            panel_size = p.get("size", "3x2")
            if "x" in panel_size:
                h = int(panel_size.split("x")[1])
            else:
                h = 2
            bottom = pos.get("y", 0) + h
            if bottom > max_y:
                max_y = bottom
        position = {"x": 0, "y": max_y}
    
    layout.setdefault("panels", []).append({
        "id": panel_id,
        "position": position,
        "size": size,
    })
    
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


def get_dashboard(enrich: bool = True) -> dict[str, Any]:
    """
    Get full dashboard with panel data merged.
    This is what the frontend needs for rendering.
    """
    layout = get_dashboard_layout()
    
    # Handle legacy format
    if layout.get("version", 1) == 1 and "cards" in layout:
        # Return legacy format as-is for backward compat
        return layout
    
    # Build full panel list with data
    panels = []
    for idx, panel_layout in enumerate(layout.get("panels", [])):
        panel_id = panel_layout.get("id")
        panel_data = get_panel_data(panel_id)
        
        if panel_data:
            panels.append({
                **panel_data,
                "position": panel_layout.get("position", {"x": 0, "y": 0}),
                "size": panel_layout.get("size", "3x2"),
                "order": panel_layout.get("order", idx),  # Include order
            })
    
    # Sort by order
    panels.sort(key=lambda p: p.get("order", 0))
    
    return {
        "version": 2,
        "panels": panels,
        "userPreferences": layout.get("userPreferences", {}),
    }


# === Legacy compatibility ===

def save_dashboard(data: dict[str, Any]) -> None:
    """Legacy: Save full dashboard (for old code paths)."""
    DASHBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
