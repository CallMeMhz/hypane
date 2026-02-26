"""Task scheduler - runs scheduled tasks using APScheduler."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def run_scheduled_task(task_id: str):
    """Execute a scheduled task."""
    from app.services import tasks_v2 as task_service

    logger.info(f"Running scheduled task: {task_id}")
    result = await task_service.execute_task(task_id)
    if result["success"]:
        logger.info(f"Task {task_id} completed successfully")
    else:
        logger.error(f"Task {task_id} failed: {result.get('error')}")


def schedule_task(task_id: str, cron_expr: str):
    """Add a task to the scheduler."""
    scheduler = get_scheduler()
    job_id = f"task_{task_id}"

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    parts = cron_expr.split()
    if len(parts) == 6:
        trigger = CronTrigger(
            second=parts[0],
            minute=parts[1],
            hour=parts[2],
            day=parts[3],
            month=parts[4],
            day_of_week=parts[5],
        )
    elif len(parts) == 5:
        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
        )
    else:
        logger.warning(f"Invalid cron expression for task {task_id}: {cron_expr}")
        return

    scheduler.add_job(
        run_scheduled_task,
        trigger=trigger,
        args=[task_id],
        id=job_id,
        replace_existing=True,
    )
    logger.info(f"Scheduled task {task_id} with cron: {cron_expr}")


def unschedule_task(task_id: str):
    """Remove a task from the scheduler."""
    scheduler = get_scheduler()
    job_id = f"task_{task_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Unscheduled task {task_id}")


async def reload_all_tasks():
    """Reload all scheduled tasks from database."""
    from app.services import tasks_v2 as task_service

    scheduler = get_scheduler()

    for job in scheduler.get_jobs():
        if job.id.startswith("task_"):
            scheduler.remove_job(job.id)

    for task in await task_service.get_scheduled_tasks():
        schedule_task(task["id"], task["schedule"])


async def start_scheduler():
    """Start the scheduler and load all tasks."""
    scheduler = get_scheduler()
    if not scheduler.running:
        await reload_all_tasks()
        scheduler.start()
        logger.info("Task scheduler started")


def stop_scheduler():
    """Stop the scheduler."""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Task scheduler stopped")
