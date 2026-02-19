"""
定时任务调度器

任务类型：
- collector: 数据采集（写入历史）
- agent: 调用 pi agent 执行复杂任务
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


def run_collector(collector: str, args: dict, task_name: str):
    """执行数据采集任务"""
    logger.info(f"Running collector: {task_name}")
    
    try:
        if collector == "weather":
            from collectors.weather import collect
            locations = args.get("locations", ["Singapore"])
            collect(locations)
        elif collector == "crypto":
            from collectors.crypto import collect
            symbols = args.get("symbols", ["BTC", "ETH"])
            collect(symbols)
        elif collector == "hackernews":
            from collectors.hackernews import collect
            limit = args.get("limit", 20)
            collect(limit)
        elif collector == "source":
            # 执行信源
            from collectors.executor import run_source_sync
            source_id = args.get("source_id")
            if source_id:
                run_source_sync(source_id)
        else:
            logger.error(f"Unknown collector: {collector}")
            return
        
        logger.info(f"Collector {task_name} completed")
    except Exception as e:
        logger.error(f"Collector {task_name} error: {e}")


def run_agent(skill_path: str, prompt: str, task_name: str):
    """执行 Agent 任务"""
    logger.info(f"Running agent task: {task_name}")
    full_path = BASE_DIR / skill_path
    extension_path = BASE_DIR / "extensions" / "dashboard-tools.ts"
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        result = subprocess.run(
            [
                "pi",
                "-p", prompt,
                "--skill", str(full_path),
                "-e", str(extension_path),
                "--mode", "text",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            logger.info(f"Agent task {task_name} completed")
            logger.debug(f"Output: {result.stdout[:500]}")
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
            
            if task["type"] == "collector":
                scheduler.add_job(
                    run_collector,
                    trigger,
                    args=[task["collector"], task.get("args", {}), task["name"]],
                    id=task["id"],
                    name=task["name"],
                )
            elif task["type"] == "agent":
                scheduler.add_job(
                    run_agent,
                    trigger,
                    args=[task["skill"], task.get("prompt", "执行任务"), task["name"]],
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
