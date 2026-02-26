"""Panel Market - 官方 Panel 模板 (v2)"""

import json
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

    template_file = panel_dir / "facade.html"
    template = ""
    if template_file.exists():
        with open(template_file, "r", encoding="utf-8") as f:
            template = f.read()

    handler_file = panel_dir / "handler.py"
    handler = ""
    if handler_file.exists():
        with open(handler_file, "r", encoding="utf-8") as f:
            handler = f.read()

    return {
        **manifest,
        "template": template,
        "handler": handler,
    }


def search_market(query: str) -> list[dict]:
    """搜索市场 Panel"""
    query = query.lower()
    panels = list_market_panels()

    results = []
    for panel in panels:
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

    results.sort(key=lambda x: x["_score"], reverse=True)

    return results


async def install_market_panel(
    panel_type: str,
    panel_id: str,
    title: str,
    storage_overrides: Optional[dict] = None,
) -> Optional[str]:
    """从市场安装 Panel 到用户数据目录。"""
    from app.sandbox import get_executor
    from app.sandbox.protocol import EventType, HandlerContext, HandlerEvent
    from app.services import panels_v2 as panels
    from app.services import storage as storage_service
    from app.services import tasks_v2 as tasks

    market_panel = get_market_panel(panel_type)
    if not market_panel:
        return None

    storage_ids = market_panel.get("storage_ids", [])
    default_storage = market_panel.get("defaultStorage", {})

    actual_storage_ids = []
    for sid in storage_ids:
        actual_sid = f"{panel_id}-{sid}"
        actual_storage_ids.append(actual_sid)

        initial_data = default_storage.get(sid, {})
        if storage_overrides and sid in storage_overrides:
            initial_data.update(storage_overrides[sid])

        await storage_service.create_storage(actual_sid, initial_data)

    template = market_panel.get("template", "")
    handler = market_panel.get("handler", "")
    for i, sid in enumerate(storage_ids):
        actual_sid = actual_storage_ids[i]
        template = template.replace(f"storage['{sid}']", f"storage['{actual_sid}']")
        template = template.replace(f'storage["{sid}"]', f'storage["{actual_sid}"]')
        template = template.replace(f"storage.get('{sid}'", f"storage.get('{actual_sid}'")
        template = template.replace(f'storage.get("{sid}"', f'storage.get("{actual_sid}"')
        handler = handler.replace(f"storage['{sid}']", f"storage['{actual_sid}']")
        handler = handler.replace(f'storage["{sid}"]', f'storage["{actual_sid}"]')
        handler = handler.replace(f"storage.get('{sid}'", f"storage.get('{actual_sid}'")
        handler = handler.replace(f'storage.get("{sid}"', f'storage.get("{actual_sid}"')

    await panels.create_panel(
        panel_id=panel_id,
        title=title,
        icon=market_panel.get("icon", "cube"),
        headerColor=market_panel.get("headerColor", "gray"),
        desc=market_panel.get("description", ""),
        size=market_panel.get("defaultSize", "3x2"),
        minSize=market_panel.get("minSize", "2x2"),
        storage_ids=actual_storage_ids,
        template=template,
        handler=handler,
    )

    if handler.strip():
        storage_data = await storage_service.load_storages_for_context(actual_storage_ids)

        executor = get_executor()
        context = HandlerContext(
            panel_id=panel_id,
            storage=storage_data,
            event=HandlerEvent(type=EventType.INIT),
        )
        result = executor.execute(handler, context)

        if result.success:
            await storage_service.save_storages_from_context(actual_storage_ids, storage_data)

    task_config = market_panel.get("task")
    if task_config and handler.strip():
        task_id = f"{panel_id}-task"
        await tasks.create_task(
            task_id=task_id,
            name=f"{title} 定时刷新",
            schedule=task_config.get("schedule", "0 */6 * * *"),
            storage_ids=actual_storage_ids,
            handler=handler,
            enabled=task_config.get("enabled", True),
        )

    return panel_id
