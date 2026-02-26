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
async def update_positions(request: PositionsUpdateRequest, dashboard_id: str = "default"):
    """Batch update panel positions after drag/resize."""
    from app.services.dashboard import update_panel_positions

    updates = {p.id: {"x": p.x, "y": p.y} for p in request.panels}
    await update_panel_positions(updates, dashboard_id)

    return {"success": True}


# === Panel CRUD ===

@router.get("")
async def list_panels():
    """List all panels."""
    return await panels.list_panels()


@router.get("/{panel_id}")
async def get_panel(panel_id: str):
    """Get panel metadata."""
    p = await panels.get_panel(panel_id)
    if not p:
        raise HTTPException(status_code=404, detail="Panel not found")
    return p


@router.post("")
async def create_panel(request: PanelCreateRequest, dashboard_id: str = "default"):
    """Create a new panel and add to specified dashboard."""
    from datetime import datetime

    from app.services.dashboard import add_panel_to_layout

    panel_id = request.id or f"panel-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    for sid in (request.storage_ids or []):
        if not await storage_service.get_storage(sid):
            await storage_service.create_storage(sid, {})

    p = await panels.create_panel(
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

    await add_panel_to_layout(panel_id, request.position, request.size or "3x2", dashboard_id)

    return p


@router.patch("/{panel_id}")
async def update_panel(panel_id: str, request: PanelUpdateRequest):
    """Update panel metadata."""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    p = await panels.update_panel(panel_id, updates)
    if not p:
        raise HTTPException(status_code=404, detail="Panel not found")
    return p


@router.delete("/{panel_id}")
async def delete_panel(panel_id: str):
    """Delete a panel with cascade soft-delete of exclusively-owned storages and tasks."""
    from app.services import tasks_v2 as task_service
    from app.services.dashboard import remove_panel_from_all_dashboards

    panel = await panels.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    panel_sids = set(panel.get("storage_ids", []))

    other_panels = [p for p in await panels.list_panels() if p["id"] != panel_id]
    all_tasks = await task_service.list_tasks()
    used_sids: set[str] = set()
    for p in other_panels:
        used_sids.update(p.get("storage_ids", []))

    deleted_tasks: list[str] = []
    for t in all_tasks:
        task_sids = set(t.get("storage_ids", []))
        if task_sids and task_sids <= panel_sids:
            await task_service.delete_task(t["id"])
            deleted_tasks.append(t["id"])
        else:
            used_sids.update(t.get("storage_ids", []))

    orphan_sids = panel_sids - used_sids
    deleted_storages: list[str] = []
    for sid in orphan_sids:
        if await storage_service.delete_storage(sid):
            deleted_storages.append(sid)

    await panels.delete_panel(panel_id)
    await remove_panel_from_all_dashboards(panel_id)

    return {
        "success": True,
        "cascade": {
            "storages": deleted_storages,
            "tasks": deleted_tasks,
        },
    }


# === Dashboard Drawer Operations ===

@router.post("/{panel_id}/add-to-dashboard")
async def add_to_dashboard(
    panel_id: str,
    dashboard_id: str = "default",
    x: int | None = None,
    y: int | None = None,
):
    """Add an existing panel to a dashboard. Supports duplicates and optional grid position."""
    from app.services.dashboard import add_panel_to_layout

    panel = await panels.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")
    position = {"x": x, "y": y} if x is not None and y is not None else None
    await add_panel_to_layout(
        panel_id, position=position, size=panel.get("size", "3x2"), dashboard_id=dashboard_id
    )
    return {"success": True}


@router.post("/{panel_id}/remove-from-dashboard")
async def remove_from_dashboard(panel_id: str, dashboard_id: str = "default"):
    """Remove a panel from a dashboard (panel itself is not deleted)."""
    from app.services.dashboard import remove_panel_from_layout

    await remove_panel_from_layout(panel_id, dashboard_id)
    return {"success": True}


# === Template & Handler ===

@router.get("/{panel_id}/template")
async def get_template(panel_id: str):
    """Get panel template."""
    from app.models.panel import Panel

    p = await Panel.load(panel_id)
    if not p:
        raise HTTPException(status_code=404, detail="Panel not found")
    return {"template": p.get_template()}


@router.put("/{panel_id}/template")
async def update_template(panel_id: str, body: dict):
    """Update panel template."""
    from app.models.panel import Panel

    p = await Panel.load(panel_id)
    if not p:
        raise HTTPException(status_code=404, detail="Panel not found")
    await p.set_template(body.get("template", ""))
    return {"success": True}


@router.get("/{panel_id}/handler")
async def get_handler(panel_id: str):
    """Get panel handler code."""
    from app.models.panel import Panel

    p = await Panel.load(panel_id)
    if not p:
        raise HTTPException(status_code=404, detail="Panel not found")
    return {"handler": p.get_handler()}


@router.put("/{panel_id}/handler")
async def update_handler(panel_id: str, body: dict):
    """Update panel handler code."""
    from app.models.panel import Panel

    p = await Panel.load(panel_id)
    if not p:
        raise HTTPException(status_code=404, detail="Panel not found")
    await p.set_handler(body.get("handler", ""))
    return {"success": True}


# === Render & Action ===

@router.get("/{panel_id}/render")
async def render_panel(panel_id: str):
    """Render panel template with storage context."""
    html = await panels.render_panel(panel_id)
    if html is None:
        raise HTTPException(status_code=404, detail="Panel not found")
    return {"html": html}


@router.post("/{panel_id}/action")
async def execute_action(panel_id: str, request: PanelActionRequest):
    """Execute panel handler action."""
    from fastapi.responses import HTMLResponse

    result = await panels.execute_action(panel_id, request.action, request.payload)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))

    return HTMLResponse(
        content=result.get("html", ""),
        headers={"HX-Trigger": f"refresh-{panel_id}"},
    )
