"""Tasks API - 定时任务管理"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException

from app.config import DATA_DIR, BASE_DIR

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

TASKS_FILE = DATA_DIR / "tasks.json"
TASK_LOGS_DIR = DATA_DIR / "task_logs"


def load_tasks() -> list[dict]:
    if not TASKS_FILE.exists():
        return []
    with open(TASKS_FILE) as f:
        return json.load(f).get("tasks", [])


def get_last_run(task_id: str) -> dict | None:
    """获取任务最后一次运行记录"""
    log_file = TASK_LOGS_DIR / f"{task_id}.json"
    if not log_file.exists():
        return None
    with open(log_file) as f:
        return json.load(f)


def save_run_log(task_id: str, result: dict):
    """保存任务运行记录"""
    TASK_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = TASK_LOGS_DIR / f"{task_id}.json"
    with open(log_file, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


@router.get("")
async def list_tasks():
    """列出所有定时任务及状态"""
    tasks = load_tasks()
    result = []
    
    for task in tasks:
        last_run = get_last_run(task["id"])
        result.append({
            "id": task["id"],
            "name": task["name"],
            "schedule": task["schedule"],
            "type": task["type"],
            "enabled": task.get("enabled", True),
            "lastRun": last_run,
        })
    
    return result


@router.post("/{task_id}/run")
async def run_task_now(task_id: str):
    """立即执行某个任务"""
    tasks = load_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    start_time = datetime.now(timezone.utc)
    error = None
    output = None
    
    try:
        if task["type"] == "collector":
            # 直接调用采集器
            collector = task["collector"]
            args = task.get("args", {})
            
            if collector == "weather":
                from collectors.weather import collect
                collect(args.get("locations", ["Singapore"]))
                output = "Weather data collected"
            elif collector == "crypto":
                from collectors.crypto import collect
                collect(args.get("symbols", ["BTC", "ETH"]))
                output = "Crypto data collected"
            elif collector == "hackernews":
                from collectors.hackernews import collect
                collect(args.get("limit", 20))
                output = "Hacker News data collected"
            else:
                raise ValueError(f"Unknown collector: {collector}")
                
        elif task["type"] == "agent":
            # 调用 pi agent
            skill_path = BASE_DIR / task["skill"]
            extension_path = BASE_DIR / "extensions" / "dashboard-tools.ts"
            prompt = task.get("prompt", "执行任务")
            
            result = subprocess.run(
                [
                    "pi",
                    "-p", prompt,
                    "--skill", str(skill_path),
                    "-e", str(extension_path),
                    "--mode", "text",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            if result.returncode == 0:
                output = result.stdout[:1000]  # 截断
            else:
                error = result.stderr[:500]
        else:
            raise ValueError(f"Unknown task type: {task['type']}")
            
    except Exception as e:
        error = str(e)
    
    end_time = datetime.now(timezone.utc)
    
    run_log = {
        "taskId": task_id,
        "startTime": start_time.isoformat().replace("+00:00", "Z"),
        "endTime": end_time.isoformat().replace("+00:00", "Z"),
        "durationMs": int((end_time - start_time).total_seconds() * 1000),
        "success": error is None,
        "output": output,
        "error": error,
    }
    
    save_run_log(task_id, run_log)
    
    return run_log
