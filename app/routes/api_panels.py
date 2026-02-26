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
    minSize: str = "2x2"
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
    minSize: str | None = None
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
        minSize=request.minSize,
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
    """Delete a panel with cascade soft-delete of exclusively-owned storages and tasks."""
    from app.services.dashboard import remove_panel_from_layout
    from app.services import tasks_v2 as task_service

    panel = panels.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    panel_sids = set(panel.get("storage_ids", []))

    # Collect storage_ids referenced by other panels
    other_panels = [p for p in panels.list_panels() if p["id"] != panel_id]
    all_tasks = task_service.list_tasks()
    used_sids: set[str] = set()
    for p in other_panels:
        used_sids.update(p.get("storage_ids", []))

    # Cascade-delete tasks whose storage_ids are a subset of this panel's
    deleted_tasks: list[str] = []
    for t in all_tasks:
        task_sids = set(t.get("storage_ids", []))
        if task_sids and task_sids <= panel_sids:
            task_service.delete_task(t["id"])
            deleted_tasks.append(t["id"])
        else:
            used_sids.update(t.get("storage_ids", []))

    # Soft-delete orphaned storages (only used by this panel)
    orphan_sids = panel_sids - used_sids
    deleted_storages: list[str] = []
    for sid in orphan_sids:
        if storage_service.delete_storage(sid):
            deleted_storages.append(sid)

    # Soft-delete the panel itself
    panels.delete_panel(panel_id)
    remove_panel_from_layout(panel_id)

    return {
        "success": True,
        "cascade": {
            "storages": deleted_storages,
            "tasks": deleted_tasks,
        },
    }


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
    from fastapi.responses import HTMLResponse

    result = panels.execute_action(panel_id, request.action, request.payload)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))

    return HTMLResponse(
        content=result.get("html", ""),
        headers={"HX-Trigger": f"refresh-{panel_id}"}
    )
