"""
Panel Scheduler

扫描所有 panel 的 handler.py，找到带 @scheduled 装饰器的方法并注册定时任务。

Handler 示例：
```python
from scheduler.decorators import scheduled

@scheduled("*/30 * * * *")
async def collect_weather(data: dict) -> dict:
    '''每30分钟采集天气'''
    # 采集逻辑
    return data
```

装饰器会自动将函数注册到 scheduler。
"""

import asyncio
import json
import importlib.util
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Callable, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
PANELS_DIR = BASE_DIR / "data" / "panels"

# Global registry for scheduled functions
# Structure: {panel_id: [(cron, func_name, func), ...]}
_scheduled_registry: dict[str, list[tuple[str, str, Callable]]] = {}


def scheduled(cron: str):
    """
    装饰器：标记函数为定时任务
    
    Args:
        cron: Cron 表达式，如 "*/30 * * * *"
    
    Usage:
        @scheduled("*/30 * * * *")
        async def collect(data: dict) -> dict:
            return data
    """
    def decorator(func: Callable) -> Callable:
        # 标记函数
        func._scheduled_cron = cron
        return func
    return decorator


def get_panel_data(panel_id: str) -> dict:
    """读取 panel data.json"""
    data_path = PANELS_DIR / panel_id / "data.json"
    if not data_path.exists():
        return {}
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_panel_data(panel_id: str, data: dict):
    """保存 panel data.json"""
    data_path = PANELS_DIR / panel_id / "data.json"
    data["updatedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_panel_handler(panel_id: str):
    """动态加载 panel 的 handler.py"""
    handler_path = PANELS_DIR / panel_id / "handler.py"
    if not handler_path.exists():
        return None
    
    try:
        spec = importlib.util.spec_from_file_location(f"panel_{panel_id}_handler", handler_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Failed to load handler for {panel_id}: {e}")
        return None


def scan_scheduled_functions(panel_id: str, module) -> list[tuple[str, str, Callable]]:
    """扫描模块中带 @scheduled 装饰器的函数"""
    scheduled_funcs = []
    
    for name in dir(module):
        if name.startswith("_"):
            continue
        
        obj = getattr(module, name)
        if callable(obj) and hasattr(obj, "_scheduled_cron"):
            cron = obj._scheduled_cron
            scheduled_funcs.append((cron, name, obj))
    
    return scheduled_funcs


async def run_scheduled_func(panel_id: str, func_name: str, func: Callable):
    """执行定时函数"""
    logger.info(f"Running {func_name} for panel: {panel_id}")
    
    try:
        data = get_panel_data(panel_id)
        
        if asyncio.iscoroutinefunction(func):
            new_data = await func(data)
        else:
            new_data = func(data)
        
        if new_data:
            save_panel_data(panel_id, new_data)
            logger.info(f"Panel {panel_id}.{func_name} completed")
        
    except Exception as e:
        logger.error(f"Panel {panel_id}.{func_name} error: {e}", exc_info=True)


def scan_all_panels() -> dict[str, list[tuple[str, str, Callable]]]:
    """扫描所有 panel，找出有定时任务的"""
    registry = {}
    
    if not PANELS_DIR.exists():
        return registry
    
    for panel_dir in PANELS_DIR.iterdir():
        if not panel_dir.is_dir():
            continue
        
        panel_id = panel_dir.name
        handler_path = panel_dir / "handler.py"
        
        if not handler_path.exists():
            continue
        
        module = load_panel_handler(panel_id)
        if module is None:
            continue
        
        scheduled_funcs = scan_scheduled_functions(panel_id, module)
        if scheduled_funcs:
            registry[panel_id] = scheduled_funcs
    
    return registry


async def main():
    """启动调度器"""
    scheduler = AsyncIOScheduler()
    
    registry = scan_all_panels()
    
    if not registry:
        logger.info("No scheduled functions found in any panel")
        # 保持运行，等待 panel 创建
    
    job_count = 0
    for panel_id, funcs in registry.items():
        data = get_panel_data(panel_id)
        title = data.get("title", panel_id)
        
        for cron, func_name, func in funcs:
            try:
                trigger = CronTrigger.from_crontab(cron)
                job_id = f"{panel_id}:{func_name}"
                
                scheduler.add_job(
                    run_scheduled_func,
                    trigger,
                    args=[panel_id, func_name, func],
                    id=job_id,
                    name=f"{title}.{func_name}",
                )
                logger.info(f"Scheduled: {title}.{func_name} ({cron})")
                job_count += 1
            except Exception as e:
                logger.error(f"Failed to schedule {panel_id}.{func_name}: {e}")
    
    scheduler.start()
    logger.info(f"Panel scheduler started with {job_count} jobs. Press Ctrl+C to exit.")
    
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    asyncio.run(main())
