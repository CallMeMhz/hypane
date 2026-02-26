"""Task service - scheduled jobs with storage binding."""

from app.models.task import Task
from app.sandbox import EventType, HandlerContext, HandlerEvent, get_executor
from app.services.storage import load_storages_for_context, save_storages_from_context
from app.services.task_scheduler import schedule_task as _schedule
from app.services.task_scheduler import unschedule_task as _unschedule


async def list_tasks() -> list[dict]:
    """List all tasks."""
    return [t.to_dict() for t in await Task.list_all()]


async def get_task(task_id: str) -> dict | None:
    """Get task by ID."""
    t = await Task.load(task_id)
    return t.to_dict() if t else None


async def create_task(
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
        handler=handler,
    )
    await t.save()

    if t.enabled and t.schedule:
        _schedule(t.id, t.schedule)

    return t.to_dict()


async def update_task(task_id: str, updates: dict) -> dict | None:
    """Update task metadata."""
    t = await Task.load(task_id)
    if not t:
        return None

    for key in ["name", "schedule", "storage_ids", "enabled"]:
        if key in updates:
            setattr(t, key, updates[key])

    await t.save()

    _unschedule(t.id)
    if t.enabled and t.schedule:
        _schedule(t.id, t.schedule)

    return t.to_dict()


async def delete_task(task_id: str) -> bool:
    """Delete a task."""
    t = await Task.load(task_id)
    if not t:
        return False
    _unschedule(task_id)
    return await t.delete()


async def execute_task(task_id: str) -> dict:
    """Execute task handler."""
    from datetime import datetime

    t = await Task.load(task_id)
    if not t:
        return {"success": False, "error": "Task not found"}

    if not t.enabled:
        return {"success": False, "error": "Task is disabled"}

    handler_code = t.get_handler()
    if not handler_code:
        return {"success": False, "error": "No handler defined"}

    storage_context = await load_storages_for_context(t.storage_ids)

    context = HandlerContext(
        task_id=task_id,
        storage=storage_context,
        event=HandlerEvent(
            type=EventType.SCHEDULE,
        ),
    )

    executor = get_executor("simple")
    result = executor.execute(handler_code, context)

    if not result.success:
        return {"success": False, "error": result.error}

    await save_storages_from_context(t.storage_ids, storage_context)

    t.last_run = datetime.now()
    await t.save()

    return {"success": True}


async def get_scheduled_tasks() -> list[dict]:
    """Get all enabled tasks with valid schedules."""
    tasks = []
    for t in await Task.list_all():
        if t.enabled and t.schedule:
            tasks.append({
                "id": t.id,
                "name": t.name,
                "schedule": t.schedule,
            })
    return tasks
