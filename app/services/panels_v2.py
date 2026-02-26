"""Panel service v2 - with storage binding support."""

from jinja2 import BaseLoader, Environment

from app.models.panel import Panel
from app.sandbox import EventType, HandlerContext, HandlerEvent, get_executor
from app.services.storage import load_storages_for_context, save_storages_from_context


async def _merge_layout(panel_dict: dict) -> dict:
    """Merge dashboard layout position/size into panel dict."""
    from app.services.dashboard import get_panel_layout

    layout = await get_panel_layout(panel_dict["id"])
    if layout:
        panel_dict["position"] = layout.get("position", {"x": 0, "y": 0})
        panel_dict["size"] = layout.get("size", panel_dict.get("size", "3x2"))
    else:
        panel_dict["position"] = {"x": 0, "y": 0}
    return panel_dict


async def list_panels() -> list[dict]:
    """List all panels with layout positions."""
    panels = await Panel.list_all()
    return [await _merge_layout(p.to_dict()) for p in panels]


async def get_panel(panel_id: str) -> dict | None:
    """Get panel by ID with layout position."""
    p = await Panel.load(panel_id)
    return await _merge_layout(p.to_dict()) if p else None


async def create_panel(
    panel_id: str,
    title: str = "Untitled",
    icon: str = "cube",
    headerColor: str = "gray",
    desc: str = "",
    size: str = "3x2",
    minSize: str = "2x2",
    storage_ids: list[str] | None = None,
    template: str = "",
    handler: str = "",
) -> dict:
    """Create a new panel."""
    p = Panel(
        id=panel_id,
        title=title,
        icon=icon,
        headerColor=headerColor,
        desc=desc,
        size=size,
        minSize=minSize,
        storage_ids=storage_ids or [],
        facade=template,
        handler=handler,
    )
    await p.save()
    return p.to_dict()


async def update_panel(panel_id: str, updates: dict) -> dict | None:
    """Update panel metadata. Position/size changes sync to dashboard layout."""
    from app.services.dashboard import update_panel_layout

    p = await Panel.load(panel_id)
    if not p:
        return None

    for key in ["title", "icon", "headerColor", "desc", "size", "minSize", "position", "storage_ids"]:
        if key in updates:
            setattr(p, key, updates[key])

    await p.save()

    if "position" in updates or "size" in updates:
        await update_panel_layout(
            panel_id,
            position=updates.get("position"),
            size=updates.get("size"),
        )

    return await _merge_layout(p.to_dict())


async def delete_panel(panel_id: str) -> bool:
    """Delete a panel."""
    p = await Panel.load(panel_id)
    if not p:
        return False
    return await p.delete()


async def render_panel(panel_id: str) -> str | None:
    """Render panel template with storage context."""
    p = await Panel.load(panel_id)
    if not p:
        return None

    template_str = p.get_template()
    if not template_str:
        return "<div class='text-muted'>No template</div>"

    storage_context = await load_storages_for_context(p.storage_ids)

    context = {
        "panel": p.to_dict(),
        "storage": storage_context,
    }
    for sid, data in storage_context.items():
        if sid.isidentifier():
            context[sid] = data

    try:
        env = Environment(loader=BaseLoader())
        template = env.from_string(template_str)
        return template.render(**context)
    except Exception as e:
        return f"<div class='text-red-500'>Template error: {e}</div>"


async def execute_action(panel_id: str, action: str, payload: dict | None = None) -> dict:
    """Execute panel handler action."""
    p = await Panel.load(panel_id)
    if not p:
        return {"success": False, "error": "Panel not found"}

    handler_code = p.get_handler()
    if not handler_code:
        return {"success": False, "error": "No handler defined"}

    storage_context = await load_storages_for_context(p.storage_ids)

    context = HandlerContext(
        panel_id=panel_id,
        storage=storage_context,
        event=HandlerEvent(
            type=EventType.ACTION,
            action=action,
            payload=payload or {},
        ),
    )

    executor = get_executor("simple")
    result = executor.execute(handler_code, context)

    if not result.success:
        return {"success": False, "error": result.error}

    await save_storages_from_context(p.storage_ids, storage_context)

    html = await render_panel(panel_id)

    return {"success": True, "html": html}
