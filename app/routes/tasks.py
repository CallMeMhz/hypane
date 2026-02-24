"""Tasks API - 定时任务管理

任务来源：
1. Panel handler 的 @scheduled 装饰器
2. data/tasks.json 的旧格式任务（已废弃）
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException

from app.config import DATA_DIR
from app.services.panels import list_panels, get_panel_handler, get_panel_data, invoke_handler

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

TASK_LOGS_DIR = DATA_DIR / "task_logs"


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


def discover_scheduled_tasks() -> list[dict]:
    """扫描所有 panel handler，发现 @scheduled 任务"""
    tasks = []
    
    for panel_id in list_panels():
        handler = get_panel_handler(panel_id)
        if handler is None:
            continue
        
        # 查找带 @scheduled 装饰器的函数
        for name in dir(handler):
            if name.startswith("_"):
                continue
            obj = getattr(handler, name)
            if callable(obj) and hasattr(obj, "_scheduled_cron"):
                panel_data = get_panel_data(panel_id) or {}
                tasks.append({
                    "id": f"{panel_id}:{name}",
                    "panelId": panel_id,
                    "functionName": name,
                    "name": f"{panel_data.get('title', panel_id)} - {name}",
                    "schedule": obj._scheduled_cron,
                    "type": "panel",
                    "enabled": True,
                })
    
    return tasks


@router.get("")
async def list_tasks():
    """列出所有定时任务及状态"""
    tasks = discover_scheduled_tasks()
    result = []
    
    for task in tasks:
        last_run = get_last_run(task["id"])
        result.append({
            "id": task["id"],
            "name": task["name"],
            "schedule": task["schedule"],
            "type": task["type"],
            "panelId": task.get("panelId"),
            "functionName": task.get("functionName"),
            "enabled": task.get("enabled", True),
            "lastRun": last_run,
        })
    
    return result


@router.post("/{task_id:path}/run")
async def run_task_now(task_id: str):
    """立即执行某个任务"""
    
    # 解析 task_id: "panel_id:function_name"
    if ":" not in task_id:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    
    panel_id, func_name = task_id.split(":", 1)
    
    # 验证任务存在
    handler = get_panel_handler(panel_id)
    if handler is None:
        raise HTTPException(status_code=404, detail="Panel handler not found")
    
    if not hasattr(handler, func_name):
        raise HTTPException(status_code=404, detail="Function not found in handler")
    
    start_time = datetime.now(timezone.utc)
    error = None
    output = None
    
    try:
        result = await invoke_handler(panel_id, func_name, {})
        if result is not None:
            output = f"Updated: {result.get('updatedAt', 'unknown')}"
        else:
            error = "Handler returned None"
    except Exception as e:
        error = str(e)
    
    end_time = datetime.now(timezone.utc)
    
    run_log = {
        "taskId": task_id,
        "panelId": panel_id,
        "functionName": func_name,
        "startTime": start_time.isoformat().replace("+00:00", "Z"),
        "endTime": end_time.isoformat().replace("+00:00", "Z"),
        "durationMs": int((end_time - start_time).total_seconds() * 1000),
        "success": error is None,
        "output": output,
        "error": error,
    }
    
    save_run_log(task_id, run_log)
    
    return run_log
