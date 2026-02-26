"""Dashboard CRUD API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.dashboard import (
    create_dashboard,
    delete_dashboard,
    list_dashboards,
    rename_dashboard,
)

router = APIRouter(prefix="/api/dashboards", tags=["dashboards"])


class DashboardCreateRequest(BaseModel):
    id: str
    name: str


class DashboardRenameRequest(BaseModel):
    name: str


@router.get("")
async def list_all():
    """List all dashboards."""
    return await list_dashboards()


@router.post("")
async def create(request: DashboardCreateRequest):
    """Create a new dashboard."""
    return await create_dashboard(request.id, request.name)


@router.patch("/{dashboard_id}")
async def rename(dashboard_id: str, request: DashboardRenameRequest):
    """Rename a dashboard."""
    if not await rename_dashboard(dashboard_id, request.name):
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"success": True}


@router.delete("/{dashboard_id}")
async def delete(dashboard_id: str):
    """Delete a dashboard (panels are not deleted)."""
    if dashboard_id == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default dashboard")
    if not await delete_dashboard(dashboard_id):
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"success": True}
