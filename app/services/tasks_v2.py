"""Task service - scheduled jobs with storage binding."""

from app.models.task import Task
from app.models.storage import Storage
from app.sandbox import get_executor, HandlerContext, HandlerEvent, EventType
from app.services.storage import load_storages_for_context, save_storages_from_context


def list_tasks() -> list[dict]:
    """List all tasks."""
    return [t.to_dict() for t in Task.list_all()]


def get_task(task_id: str) -> dict | None:
    """Get task by ID."""
    t = Task.load(task_id)
    return t.to_dict() if t else None


def create_task(
    task_id: str,
    name: str = "Untitled Task",
    schedule: str = "",
    storage_ids: list[str] | None = None,
    handler: str = "",
    enabled: bool = True,
) -> dict:
    """Create a new task."""
    t = Task(
        id=task_id,
        name=name,
        schedule=schedule,
        storage_ids=storage_ids or [],
        enabled=enabled,
    )
    t.save()
    
    if handler:
        t.set_handler(handler)
    
    return t.to_dict()


def update_task(task_id: str, updates: dict) -> dict | None:
    """Update task metadata."""
    t = Task.load(task_id)
    if not t:
        return None
    
    for key in ["name", "schedule", "storage_ids", "enabled"]:
        if key in updates:
            setattr(t, key, updates[key])
    
    t.save()
    return t.to_dict()


def delete_task(task_id: str) -> bool:
    """Delete a task."""
    t = Task.load(task_id)
    if not t:
        return False
    return t.delete()


def execute_task(task_id: str) -> dict:
    """
    Execute task handler.
    
    Returns:
        {
            "success": bool,
            "error": str | None,
        }
    """
    from datetime import datetime
    
    t = Task.load(task_id)
    if not t:
        return {"success": False, "error": "Task not found"}
    
    if not t.enabled:
        return {"success": False, "error": "Task is disabled"}
    
    handler_code = t.get_handler()
    if not handler_code:
        return {"success": False, "error": "No handler defined"}
    
    # Load storages
    storage_context = load_storages_for_context(t.storage_ids)
    
    # Build handler context
    context = HandlerContext(
        task_id=task_id,
        storage=storage_context,
        event=HandlerEvent(
            type=EventType.SCHEDULE,
        )
    )
    
    # Execute in sandbox
    executor = get_executor("simple")
    result = executor.execute(handler_code, context)
    
    if not result.success:
        return {"success": False, "error": result.error}
    
    # Save modified storages
    save_storages_from_context(t.storage_ids, storage_context)
    
    # Update last_run
    t.last_run = datetime.now()
    t.save()
    
    return {"success": True}


def get_scheduled_tasks() -> list[dict]:
    """Get all enabled tasks with valid schedules."""
    tasks = []
    for t in Task.list_all():
        if t.enabled and t.schedule:
            tasks.append({
                "id": t.id,
                "name": t.name,
                "schedule": t.schedule,
            })
    return tasks
