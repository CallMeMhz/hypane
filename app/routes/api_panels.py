"""Panel API routes - v2 with storage binding."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import panels_v2 as panels
from app.services import storage as storage_service

router = APIRouter(prefix="/api/panels", tags=["panels"])


# === Request Models ===

class PanelCreateRequest(BaseModel):
    id: str | None = None
    title: str = "Untitled"
    icon: str = "cube"
    headerColor: str = "gray"
    desc: str = ""
    size: str = "3x2"
    position: dict | None = None
    storage_ids: list[str] | None = None
    template: str = ""
    handler: str = ""


class PanelUpdateRequest(BaseModel):
    title: str | None = None
    icon: str | None = None
    headerColor: str | None = None
    desc: str | None = None
    size: str | None = None
    position: dict | None = None
    storage_ids: list[str] | None = None


class PanelActionRequest(BaseModel):
    action: str
    payload: dict | None = None


# === Batch Position Update (must be before /{panel_id} routes) ===

class PositionUpdate(BaseModel):
    id: str
    x: int
    y: int


class PositionsUpdateRequest(BaseModel):
    panels: list[PositionUpdate]


@router.post("/positions")
async def update_positions(request: PositionsUpdateRequest):
    """Batch update panel positions after drag/resize."""
    from app.services.dashboard import update_panel_positions
    
    updates = {p.id: {"x": p.x, "y": p.y} for p in request.panels}
    update_panel_positions(updates)
    
    return {"success": True}


# === Panel CRUD ===

@router.get("")
async def list_panels():
    """List all panels."""
    return panels.list_panels()


@router.get("/{panel_id}")
async def get_panel(panel_id: str):
    """Get panel metadata."""
    p = panels.get_panel(panel_id)
    if not p:
        raise HTTPException(status_code=404, detail="Panel not found")
    return p


@router.post("")
async def create_panel(request: PanelCreateRequest):
    """Create a new panel."""
    from datetime import datetime
    from app.services.dashboard import add_panel_to_layout
    
    # Generate ID if not provided
    panel_id = request.id or f"panel-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create any storage that doesn't exist yet
    for sid in (request.storage_ids or []):
        if not storage_service.get_storage(sid):
            storage_service.create_storage(sid, {})
    
    p = panels.create_panel(
        panel_id=panel_id,
        title=request.title,
        icon=request.icon,
        headerColor=request.headerColor,
        desc=request.desc,
        size=request.size,
        storage_ids=request.storage_ids,
        template=request.template,
        handler=request.handler,
    )
    
    # Add to dashboard layout
    add_panel_to_layout(panel_id, request.position, request.size or "3x2")
    
    return p


@router.patch("/{panel_id}")
async def update_panel(panel_id: str, request: PanelUpdateRequest):
    """Update panel metadata."""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    p = panels.update_panel(panel_id, updates)
    if not p:
        raise HTTPException(status_code=404, detail="Panel not found")
    return p


@router.delete("/{panel_id}")
async def delete_panel(panel_id: str):
    """Delete a panel."""
    from app.services.dashboard import remove_panel_from_layout
    
    if not panels.delete_panel(panel_id):
        raise HTTPException(status_code=404, detail="Panel not found")
    
    # Remove from layout
    remove_panel_from_layout(panel_id)
    
    return {"success": True}


# === Template & Handler ===

@router.get("/{panel_id}/template")
async def get_template(panel_id: str):
    """Get panel template."""
    from app.models.panel import Panel
    p = Panel.load(panel_id)
    if not p:
        raise HTTPException(status_code=404, detail="Panel not found")
    return {"template": p.get_template()}


@router.put("/{panel_id}/template")
async def update_template(panel_id: str, body: dict):
    """Update panel template."""
    from app.models.panel import Panel
    p = Panel.load(panel_id)
    if not p:
        raise HTTPException(status_code=404, detail="Panel not found")
    p.set_template(body.get("template", ""))
    return {"success": True}


@router.get("/{panel_id}/handler")
async def get_handler(panel_id: str):
    """Get panel handler code."""
    from app.models.panel import Panel
    p = Panel.load(panel_id)
    if not p:
        raise HTTPException(status_code=404, detail="Panel not found")
    return {"handler": p.get_handler()}


@router.put("/{panel_id}/handler")
async def update_handler(panel_id: str, body: dict):
    """Update panel handler code."""
    from app.models.panel import Panel
    p = Panel.load(panel_id)
    if not p:
        raise HTTPException(status_code=404, detail="Panel not found")
    p.set_handler(body.get("handler", ""))
    return {"success": True}


# === Render & Action ===

@router.get("/{panel_id}/render")
async def render_panel(panel_id: str):
    """Render panel template with storage context."""
    html = panels.render_panel(panel_id)
    if html is None:
        raise HTTPException(status_code=404, detail="Panel not found")
    return {"html": html}


@router.post("/{panel_id}/action")
async def execute_action(panel_id: str, request: PanelActionRequest):
    """
    Execute panel handler action.
    
    Handler receives: on_action(action, payload, storage)
    Storage is modified in-place, then saved.
    Returns re-rendered panel HTML with HX-Trigger to refresh panel.
    """
    from fastapi.responses import JSONResponse
    
    result = panels.execute_action(panel_id, request.action, request.payload)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    # Return with HX-Trigger header to refresh the panel
    return JSONResponse(
        content=result,
        headers={"HX-Trigger": f"refresh-{panel_id}"}
    )
