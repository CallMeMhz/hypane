"""Panel service v2 - with storage binding support."""

from pathlib import Path
from jinja2 import Environment, BaseLoader

from app.models.panel import Panel
from app.models.storage import Storage
from app.sandbox import get_executor, HandlerContext, HandlerEvent, EventType
from app.services.storage import load_storages_for_context, save_storages_from_context


def list_panels() -> list[dict]:
    """List all panels."""
    return [p.to_dict() for p in Panel.list_all()]


def get_panel(panel_id: str) -> dict | None:
    """Get panel by ID."""
    p = Panel.load(panel_id)
    return p.to_dict() if p else None


def create_panel(
    panel_id: str,
    title: str = "Untitled",
    icon: str = "cube",
    headerColor: str = "gray",
    desc: str = "",
    size: str = "3x2",
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
        storage_ids=storage_ids or [],
    )
    p.save()
    
    if template:
        p.set_template(template)
    if handler:
        p.set_handler(handler)
    
    return p.to_dict()


def update_panel(panel_id: str, updates: dict) -> dict | None:
    """Update panel metadata."""
    p = Panel.load(panel_id)
    if not p:
        return None
    
    for key in ["title", "icon", "headerColor", "desc", "size", "position", "storage_ids"]:
        if key in updates:
            setattr(p, key, updates[key])
    
    p.save()
    return p.to_dict()


def delete_panel(panel_id: str) -> bool:
    """Delete a panel."""
    p = Panel.load(panel_id)
    if not p:
        return False
    return p.delete()


def render_panel(panel_id: str) -> str | None:
    """
    Render panel template with storage context.
    
    Returns rendered HTML string.
    """
    p = Panel.load(panel_id)
    if not p:
        return None
    
    template_str = p.get_template()
    if not template_str:
        return "<div class='text-muted'>No template</div>"
    
    # Load storages
    storage_context = load_storages_for_context(p.storage_ids)
    
    # Build Jinja2 context
    context = {
        "panel": p.to_dict(),
        "storage": storage_context,  # Access via storage['id']['field']
    }
    # Also add each storage directly for convenience (if ID is valid Python identifier)
    for sid, data in storage_context.items():
        if sid.isidentifier():
            context[sid] = data
    
    # Render template
    try:
        env = Environment(loader=BaseLoader())
        template = env.from_string(template_str)
        return template.render(**context)
    except Exception as e:
        return f"<div class='text-red-500'>Template error: {e}</div>"


def execute_action(panel_id: str, action: str, payload: dict | None = None) -> dict:
    """
    Execute panel handler action.
    
    Returns:
        {
            "success": bool,
            "error": str | None,
            "html": str | None  # Re-rendered panel HTML
        }
    """
    p = Panel.load(panel_id)
    if not p:
        return {"success": False, "error": "Panel not found"}
    
    handler_code = p.get_handler()
    if not handler_code:
        return {"success": False, "error": "No handler defined"}
    
    # Load storages
    storage_context = load_storages_for_context(p.storage_ids)
    
    # Build handler context
    context = HandlerContext(
        panel_id=panel_id,
        storage=storage_context,
        event=HandlerEvent(
            type=EventType.ACTION,
            action=action,
            payload=payload or {},
        )
    )
    
    # Execute in sandbox
    executor = get_executor("simple")
    result = executor.execute(handler_code, context)
    
    if not result.success:
        return {"success": False, "error": result.error}
    
    # Save modified storages
    save_storages_from_context(p.storage_ids, storage_context)
    
    # Re-render panel
    html = render_panel(panel_id)
    
    return {"success": True, "html": html}
