"""Task API routes (v2 - storage binding)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import tasks_v2 as task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class CreateTaskRequest(BaseModel):
    id: str
    name: str = "Untitled Task"
    schedule: str = ""  # Cron expression
    storage_ids: list[str] | None = None
    handler: str | None = None
    enabled: bool = True


class UpdateTaskRequest(BaseModel):
    name: str | None = None
    schedule: str | None = None
    storage_ids: list[str] | None = None
    enabled: bool | None = None


class UpdateHandlerRequest(BaseModel):
    handler: str


@router.get("")
async def list_tasks():
    """List all tasks."""
    return task_service.list_tasks()


@router.get("/scheduled")
async def get_scheduled_tasks():
    """Get all enabled tasks with schedules (for scheduler)."""
    return task_service.get_scheduled_tasks()


@router.get("/{task_id}")
async def get_task(task_id: str):
    """Get a task by ID."""
    t = task_service.get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return t


@router.post("")
async def create_task(request: CreateTaskRequest):
    """Create a new task."""
    if task_service.get_task(request.id):
        raise HTTPException(status_code=409, detail="Task already exists")
    return task_service.create_task(
        task_id=request.id,
        name=request.name,
        schedule=request.schedule,
        storage_ids=request.storage_ids,
        handler=request.handler or "",
        enabled=request.enabled,
    )


@router.patch("/{task_id}")
async def update_task(task_id: str, request: UpdateTaskRequest):
    """Update task metadata."""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    t = task_service.update_task(task_id, updates)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return t


@router.put("/{task_id}/handler")
async def update_task_handler(task_id: str, request: UpdateHandlerRequest):
    """Update task handler code."""
    from app.models.task import Task
    t = Task.load(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    t.set_handler(request.handler)
    return {"success": True}


@router.post("/{task_id}/run")
async def run_task(task_id: str):
    """Manually run a task."""
    result = task_service.execute_task(task_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Task execution failed"))
    return result


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Delete a task."""
    if not task_service.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}
