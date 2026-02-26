"""Console route - resource relationship graph."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.services import panels_v2
from app.services import storage as storage_service
from app.services import tasks_v2 as task_service

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/console", response_class=HTMLResponse)
async def console_page(request: Request):
    """Render the resource console page."""
    panels = panels_v2.list_panels()
    storages = storage_service.list_storages()
    tasks = task_service.list_tasks()
    return templates.TemplateResponse(
        "console.html",
        {
            "request": request,
            "panels": panels,
            "storages": storages,
            "tasks": tasks,
        },
    )
