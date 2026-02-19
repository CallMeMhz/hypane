"""
信源执行器

根据信源配置执行抓取，支持：
1. 使用预置抓取能力
2. 使用 Agent 生成的自定义采集器
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Optional

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SOURCES_DIR = DATA_DIR / "sources"

# 添加项目根目录到 path
sys.path.insert(0, str(BASE_DIR))


def get_source(source_id: str) -> Optional[dict]:
    """读取信源配置"""
    file = SOURCES_DIR / f"{source_id}.json"
    if not file.exists():
        return None
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)


async def run_source(source_id: str) -> dict:
    """
    执行信源抓取
    
    Returns:
        {"success": bool, "data": Any, "error": str}
    """
    source = get_source(source_id)
    if not source:
        return {"success": False, "error": f"Source not found: {source_id}"}
    
    if not source.get("enabled", True):
        return {"success": False, "error": "Source is disabled"}
    
    # 如果有自定义采集器，使用它
    if source.get("collector"):
        return await _run_custom_collector(source)
    
    # 否则使用预置抓取能力
    return await _run_preset_fetch(source)


async def _run_preset_fetch(source: dict) -> dict:
    """使用预置能力抓取"""
    from collectors.presets import fetch_api, fetch_webpage, fetch_browser
    from app.services.history import write_history
    
    config = source.get("fetchConfig", {})
    fetch_type = config.get("type", "api")
    url = config.get("url")
    
    if not url:
        return {"success": False, "error": "No URL configured"}
    
    try:
        if fetch_type == "api":
            result = await fetch_api(
                url=url,
                method=config.get("method", "GET"),
                headers=config.get("headers"),
                params=config.get("params"),
            )
        elif fetch_type == "webpage":
            result = await fetch_webpage(
                url=url,
                selectors=config.get("selectors"),
                headers=config.get("headers"),
            )
        elif fetch_type == "browser":
            result = await fetch_browser(
                url=url,
                script=config.get("script"),
                wait_selector=config.get("waitSelector"),
            )
        else:
            return {"success": False, "error": f"Unknown fetch type: {fetch_type}"}
        
        # 写入历史
        if result.get("success"):
            write_history(
                source=f"sources/{source['id']}",
                data=result["data"],
                granularity="hour",
            )
        
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _run_custom_collector(source: dict) -> dict:
    """运行自定义采集器"""
    collector_path = BASE_DIR / source["collector"]
    
    if not collector_path.exists():
        return {"success": False, "error": f"Collector not found: {collector_path}"}
    
    try:
        # 动态加载模块
        spec = importlib.util.spec_from_file_location("collector", collector_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["collector"] = module
        spec.loader.exec_module(module)
        
        # 调用 collect 函数
        if hasattr(module, "collect"):
            result = module.collect(source)
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": "Collector has no 'collect' function"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_source_sync(source_id: str) -> dict:
    """同步版本"""
    import asyncio
    return asyncio.run(run_source(source_id))
