"""
定时任务调度器

根据 data/tasks.json 配置执行定时任务。
任务类型：
- script: 执行 Python 脚本
- agent: 调用 pi agent 执行 skill
"""

import json
import subprocess
import logging
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
TASKS_FILE = BASE_DIR / "data" / "tasks.json"
SESSIONS_DIR = BASE_DIR / "data" / "sessions"


def load_tasks() -> list[dict]:
    """加载任务配置"""
    if not TASKS_FILE.exists():
        logger.warning(f"Tasks file not found: {TASKS_FILE}")
        return []
    
    with open(TASKS_FILE) as f:
        return json.load(f).get("tasks", [])


def run_script(script_path: str, task_name: str):
    """执行脚本任务"""
    logger.info(f"Running script task: {task_name}")
    full_path = BASE_DIR / script_path
    
    try:
        result = subprocess.run(
            ["python", str(full_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            logger.info(f"Task {task_name} completed successfully")
        else:
            logger.error(f"Task {task_name} failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        logger.error(f"Task {task_name} timed out")
    except Exception as e:
        logger.error(f"Task {task_name} error: {e}")


def run_agent(skill_path: str, task_name: str):
    """执行 Agent 任务"""
    logger.info(f"Running agent task: {task_name}")
    full_path = BASE_DIR / skill_path
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        result = subprocess.run(
            [
                "pi",
                "-p", f"执行定时任务: {task_name}",
                "--skill", str(full_path),
                "--session-dir", str(SESSIONS_DIR),
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            logger.info(f"Agent task {task_name} completed successfully")
        else:
            logger.error(f"Agent task {task_name} failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        logger.error(f"Agent task {task_name} timed out")
    except Exception as e:
        logger.error(f"Agent task {task_name} error: {e}")


def main():
    """启动调度器"""
    scheduler = BlockingScheduler()
    tasks = load_tasks()
    
    for task in tasks:
        if not task.get("enabled", True):
            logger.info(f"Task {task['id']} is disabled, skipping")
            continue
        
        try:
            trigger = CronTrigger.from_crontab(task["schedule"])
            
            if task["type"] == "script":
                scheduler.add_job(
                    run_script,
                    trigger,
                    args=[task["script"], task["name"]],
                    id=task["id"],
                    name=task["name"],
                )
            elif task["type"] == "agent":
                scheduler.add_job(
                    run_agent,
                    trigger,
                    args=[task["skill"], task["name"]],
                    id=task["id"],
                    name=task["name"],
                )
            
            logger.info(f"Scheduled task: {task['name']} ({task['schedule']})")
        except Exception as e:
            logger.error(f"Failed to schedule task {task['id']}: {e}")
    
    logger.info("Scheduler started. Press Ctrl+C to exit.")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
