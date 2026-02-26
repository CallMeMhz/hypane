"""Console route - resource relationship list."""

from collections import defaultdict

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

    # Build reverse map: storage_id → list of {type, id, name} that reference it
    storage_refs: dict[str, list[dict]] = defaultdict(list)
    for p in panels:
        for sid in p.get("storage_ids", []):
            storage_refs[sid].append(
                {"type": "panel", "id": p["id"], "name": p.get("title", p["id"])}
            )
    for t in tasks:
        for sid in t.get("storage_ids", []):
            storage_refs[sid].append(
                {"type": "task", "id": t["id"], "name": t.get("name", t["id"])}
            )

    # Mark orphan storages (not referenced by any panel or task)
    all_storage_ids = {s["id"] for s in storages}
    referenced_ids = set(storage_refs.keys())
    orphan_ids = all_storage_ids - referenced_ids

    return templates.TemplateResponse(
        "console.html",
        {
            "request": request,
            "panels": panels,
            "storages": storages,
            "tasks": tasks,
            "storage_refs": dict(storage_refs),
            "orphan_ids": list(orphan_ids),
        },
    )
