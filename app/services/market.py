"""Panel Market - 官方 Panel 模板"""

import json
import shutil
from pathlib import Path
from typing import Optional

from app.config import BASE_DIR

MARKET_DIR = BASE_DIR / "market"


def list_market_panels() -> list[dict]:
    """列出所有市场 Panel"""
    panels = []
    
    if not MARKET_DIR.exists():
        return panels
    
    for panel_dir in MARKET_DIR.iterdir():
        if not panel_dir.is_dir():
            continue
        
        manifest_file = panel_dir / "manifest.json"
        if not manifest_file.exists():
            continue
        
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        panels.append({
            "id": manifest.get("id"),
            "name": manifest.get("name"),
            "description": manifest.get("description"),
            "icon": manifest.get("icon"),
            "headerColor": manifest.get("headerColor"),
            "defaultSize": manifest.get("defaultSize"),
            "minSize": manifest.get("minSize"),
            "keywords": manifest.get("keywords", []),
        })
    
    return panels


def get_market_panel(panel_type: str) -> Optional[dict]:
    """获取市场 Panel 详情"""
    panel_dir = MARKET_DIR / panel_type
    manifest_file = panel_dir / "manifest.json"
    
    if not manifest_file.exists():
        return None
    
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    # 读取 facade
    facade_file = panel_dir / "facade.html"
    facade = ""
    if facade_file.exists():
        with open(facade_file, "r", encoding="utf-8") as f:
            facade = f.read()
    
    # 读取 handler
    handler_file = panel_dir / "handler.py"
    handler = None
    if handler_file.exists():
        with open(handler_file, "r", encoding="utf-8") as f:
            handler = f.read()
    
    return {
        **manifest,
        "facade": facade,
        "handler": handler,
    }


def search_market(query: str) -> list[dict]:
    """搜索市场 Panel"""
    query = query.lower()
    panels = list_market_panels()
    
    results = []
    for panel in panels:
        # 匹配名称、描述、关键词
        score = 0
        if query in panel["name"].lower():
            score += 10
        if query in panel.get("description", "").lower():
            score += 5
        for kw in panel.get("keywords", []):
            if query in kw.lower():
                score += 8
        
        if score > 0:
            results.append({**panel, "_score": score})
    
    # 按匹配度排序
    results.sort(key=lambda x: x["_score"], reverse=True)
    
    return results


def install_market_panel(
    panel_type: str,
    panel_id: str,
    title: str,
    data_overrides: Optional[dict] = None,
) -> Optional[str]:
    """
    从市场安装 Panel 到用户数据目录。
    
    Args:
        panel_type: 市场模板类型 (如 "todo", "weather")
        panel_id: 新 Panel 的 ID
        title: Panel 标题
        data_overrides: 覆盖默认数据的字段
    
    Returns:
        panel_id if success, None otherwise
    """
    from app.services.panels import PANELS_DIR, get_panel_data
    from datetime import datetime, timezone
    
    market_panel = get_market_panel(panel_type)
    if not market_panel:
        return None
    
    # 创建 panel 目录
    panel_dir = PANELS_DIR / panel_id
    panel_dir.mkdir(parents=True, exist_ok=True)
    
    # 准备 data.json
    data = {
        "id": panel_id,
        "title": title,
        "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "icon": market_panel.get("icon", "box"),
        "headerColor": market_panel.get("headerColor", "gray"),
        "minSize": market_panel.get("minSize", "2x2"),
        "desc": market_panel.get("description", ""),
        "marketType": panel_type,  # 标记来源
        **market_panel.get("defaultData", {}),
    }
    
    # 应用覆盖
    if data_overrides:
        data.update(data_overrides)
    
    # 写入文件
    with open(panel_dir / "data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 复制 facade
    if market_panel.get("facade"):
        with open(panel_dir / "facade.html", "w", encoding="utf-8") as f:
            f.write(market_panel["facade"])
    
    # 复制 handler
    if market_panel.get("handler"):
        with open(panel_dir / "handler.py", "w", encoding="utf-8") as f:
            f.write(market_panel["handler"])
    
    return panel_id
