"""Panel API routes."""

import json
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.panels import (
    create_panel,
    delete_panel,
    get_panel,
    get_panel_data,
    get_panel_facade,
    save_panel_data,
    save_panel_facade,
    save_panel_handler,
    invoke_handler,
    update_panel_data,
    panel_exists,
)
from app.services.dashboard import (
    add_panel_to_layout,
    remove_panel_from_layout,
    update_panel_layout,
    get_panel_layout,
)
from app.services.snapshots import create_snapshot
from app.services.dashboard import get_dashboard, save_dashboard

router = APIRouter(prefix="/api/panels", tags=["panels"])


# === Request Models ===

class CreatePanelRequest(BaseModel):
    title: str
    desc: Optional[str] = None  # Natural language description for agent
    icon: Optional[str] = "box"  # Lucide icon name
    headerColor: Optional[str] = "gray"  # Color preset name
    facade: str  # HTML
    data: Optional[dict] = None
    handler: Optional[str] = None  # Python code
    size: Optional[str] = "3x2"
    position: Optional[dict] = None  # {x, y}
    minSize: Optional[str] = None


class UpdatePanelRequest(BaseModel):
    title: Optional[str] = None
    desc: Optional[str] = None
    icon: Optional[str] = None
    headerColor: Optional[str] = None
    facade: Optional[str] = None
    data: Optional[dict] = None
    handler: Optional[str] = None
    size: Optional[str] = None
    position: Optional[dict] = None


class PanelActionRequest(BaseModel):
    action: str
    payload: Optional[dict] = None


# === Endpoints ===

@router.get("")
async def list_panels_api():
    """List all panels with their data."""
    dashboard = get_dashboard()
    return dashboard.get("panels", dashboard.get("cards", []))


@router.post("")
async def create_panel_api(request: CreatePanelRequest):
    """Create a new panel."""
    # Prepare data with icon, headerColor, desc
    panel_data = request.data or {}
    panel_data["icon"] = request.icon or "box"
    panel_data["headerColor"] = request.headerColor or "gray"
    if request.desc:
        panel_data["desc"] = request.desc
    if request.minSize:
        panel_data["minSize"] = request.minSize
    
    # Create panel
    panel_id = create_panel(
        title=request.title,
        facade_html=request.facade,
        data=panel_data,
        handler_code=request.handler,
    )
    
    # Add to layout
    add_panel_to_layout(panel_id, request.position, request.size or "3x2")
    
    # Create snapshot
    dashboard = get_dashboard()
    create_snapshot(
        dashboard,
        action="create",
        details=f"Created panel: {request.title}",
        card_id=panel_id,
    )
    
    return get_panel(panel_id)


@router.get("/{panel_id}")
async def get_panel_api(panel_id: str):
    """Get a panel by ID."""
    panel = get_panel(panel_id)
    if panel is None:
        raise HTTPException(status_code=404, detail="Panel not found")
    
    # Include layout info
    layout = get_panel_layout(panel_id)
    if layout:
        panel["position"] = layout.get("position", {"x": 0, "y": 0})
        panel["size"] = layout.get("size", "3x2")
    
    return panel


@router.patch("/{panel_id}")
async def update_panel_api(panel_id: str, request: UpdatePanelRequest):
    """Update a panel."""
    if not panel_exists(panel_id):
        raise HTTPException(status_code=404, detail="Panel not found")
    
    # Update data fields
    updates = {}
    if request.title is not None:
        updates["title"] = request.title
    if request.desc is not None:
        updates["desc"] = request.desc
    if request.icon is not None:
        updates["icon"] = request.icon
    if request.headerColor is not None:
        updates["headerColor"] = request.headerColor
    if request.data is not None:
        updates.update(request.data)
    
    if updates:
        update_panel_data(panel_id, updates)
    
    # Update facade
    if request.facade is not None:
        save_panel_facade(panel_id, request.facade)
    
    # Update handler
    if request.handler is not None:
        save_panel_handler(panel_id, request.handler)
    
    # Update layout
    if request.position is not None or request.size is not None:
        update_panel_layout(panel_id, request.position, request.size)
    
    # Snapshot
    dashboard = get_dashboard()
    panel_data = get_panel_data(panel_id)
    create_snapshot(
        dashboard,
        action="update",
        details=f"Updated panel: {panel_data.get('title', panel_id)}",
        card_id=panel_id,
    )
    
    return get_panel(panel_id)


@router.delete("/{panel_id}")
async def delete_panel_api(panel_id: str):
    """Delete a panel."""
    if not panel_exists(panel_id):
        raise HTTPException(status_code=404, detail="Panel not found")
    
    panel_data = get_panel_data(panel_id)
    title = panel_data.get("title", panel_id) if panel_data else panel_id
    
    # Remove from layout
    remove_panel_from_layout(panel_id)
    
    # Delete panel files
    delete_panel(panel_id)
    
    # Snapshot
    dashboard = get_dashboard()
    create_snapshot(
        dashboard,
        action="delete",
        details=f"Deleted panel: {title}",
        card_id=panel_id,
    )
    
    return {"success": True, "id": panel_id}


@router.post("/{panel_id}/action")
async def panel_action_api(panel_id: str, request: PanelActionRequest):
    """
    Execute a panel action via its handler.
    """
    if not panel_exists(panel_id):
        raise HTTPException(status_code=404, detail="Panel not found")
    
    result = await invoke_handler(panel_id, request.action, request.payload or {})
    
    if result is None:
        # No handler or handler returned None - just return current data
        data = get_panel_data(panel_id)
        return {"success": True, "data": data}
    
    return {"success": True, "data": result}


# === Facade/Data/Handler specific endpoints ===

@router.get("/{panel_id}/facade")
async def get_facade_api(panel_id: str):
    """Get panel facade HTML."""
    facade = get_panel_facade(panel_id)
    if facade is None:
        raise HTTPException(status_code=404, detail="Panel or facade not found")
    return {"facade": facade}


@router.put("/{panel_id}/facade")
async def update_facade_api(panel_id: str, body: dict):
    """Update panel facade HTML."""
    if not panel_exists(panel_id):
        raise HTTPException(status_code=404, detail="Panel not found")
    
    facade = body.get("facade", "")
    save_panel_facade(panel_id, facade)
    return {"success": True}


@router.get("/{panel_id}/data")
async def get_data_api(panel_id: str):
    """Get panel data."""
    data = get_panel_data(panel_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Panel not found")
    return data


@router.patch("/{panel_id}/data")
async def update_data_api(panel_id: str, body: dict):
    """Update panel data (merge)."""
    if not panel_exists(panel_id):
        raise HTTPException(status_code=404, detail="Panel not found")
    
    result = update_panel_data(panel_id, body)
    return result


@router.put("/{panel_id}/handler")
async def update_handler_api(panel_id: str, body: dict):
    """Update panel handler code."""
    if not panel_exists(panel_id):
        raise HTTPException(status_code=404, detail="Panel not found")
    
    code = body.get("handler", "")
    save_panel_handler(panel_id, code)
    return {"success": True}


# === Batch Position Update ===

class PanelPosition(BaseModel):
    id: str
    position: dict


class UpdatePositionsRequest(BaseModel):
    panels: list[PanelPosition]


@router.post("/positions")
async def update_panel_positions(request: UpdatePositionsRequest):
    """Batch update panel positions."""
    for item in request.panels:
        update_panel_layout(item.id, position=item.position)
    
    return {"success": True, "updated": len(request.panels)}


# === Batch Order Update ===

class PanelOrder(BaseModel):
    id: str
    order: int


class UpdateOrderRequest(BaseModel):
    panels: list[PanelOrder]


@router.post("/order")
async def update_panel_order(request: UpdateOrderRequest):
    """Batch update panel order."""
    from app.services.dashboard import get_dashboard, save_dashboard
    
    dashboard = get_dashboard()
    panels = dashboard.get("panels", dashboard.get("cards", []))
    
    # Create lookup
    order_map = {item.id: item.order for item in request.panels}
    
    # Update order for each panel
    for panel in panels:
        panel_id = panel.get("id", "")
        # Strip panel- prefix if present
        clean_id = panel_id.replace("panel-", "") if panel_id.startswith("panel-") else panel_id
        
        if panel_id in order_map:
            panel["order"] = order_map[panel_id]
        elif clean_id in order_map:
            panel["order"] = order_map[clean_id]
    
    # Sort panels by order
    panels.sort(key=lambda p: p.get("order", 0))
    
    # Save
    dashboard["panels"] = panels
    save_dashboard(dashboard)
    
    return {"success": True, "updated": len(request.panels)}
