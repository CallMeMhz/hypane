"""Panel service - manages panel lifecycle and dynamic handler loading."""

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional
import uuid

from app.config import DATA_DIR

PANELS_DIR = DATA_DIR / "panels"

# Handler cache: {panel_id: (mtime, module)}
_handler_cache: dict[str, tuple[float, Any]] = {}


def ensure_panels_dir():
    """Ensure panels directory exists."""
    PANELS_DIR.mkdir(parents=True, exist_ok=True)


def get_panel_dir(panel_id: str) -> Path:
    """Get panel directory path."""
    return PANELS_DIR / panel_id


def panel_exists(panel_id: str) -> bool:
    """Check if panel exists."""
    return get_panel_dir(panel_id).exists()


def list_panels() -> list[str]:
    """List all panel IDs."""
    ensure_panels_dir()
    return [d.name for d in PANELS_DIR.iterdir() if d.is_dir()]


def generate_panel_id(panel_type: str) -> str:
    """Generate a unique panel ID."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    short_uuid = uuid.uuid4().hex[:4]
    return f"{panel_type}-{timestamp}-{short_uuid}"


# === Data (data.json) ===

def get_panel_data(panel_id: str) -> Optional[dict]:
    """Load panel data.json."""
    data_file = get_panel_dir(panel_id) / "data.json"
    if not data_file.exists():
        return None
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_panel_data(panel_id: str, data: dict) -> None:
    """Save panel data.json."""
    panel_dir = get_panel_dir(panel_id)
    panel_dir.mkdir(parents=True, exist_ok=True)
    
    data["updatedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    data_file = panel_dir / "data.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_panel_data(panel_id: str, updates: dict) -> Optional[dict]:
    """Merge updates into panel data."""
    data = get_panel_data(panel_id)
    if data is None:
        return None
    
    # Deep merge for nested dicts
    for key, value in updates.items():
        if key in data and isinstance(data[key], dict) and isinstance(value, dict):
            data[key].update(value)
        else:
            data[key] = value
    
    save_panel_data(panel_id, data)
    return data


# === Facade (facade.html) ===

def get_panel_facade(panel_id: str) -> Optional[str]:
    """Load panel facade.html."""
    facade_file = get_panel_dir(panel_id) / "facade.html"
    if not facade_file.exists():
        return None
    with open(facade_file, "r", encoding="utf-8") as f:
        return f.read()


def save_panel_facade(panel_id: str, html: str) -> None:
    """Save panel facade.html."""
    panel_dir = get_panel_dir(panel_id)
    panel_dir.mkdir(parents=True, exist_ok=True)
    
    # Replace __PANEL_ID__ placeholder
    html = html.replace("__PANEL_ID__", panel_id)
    html = html.replace("__CARD_ID__", panel_id)  # Backward compat
    
    facade_file = panel_dir / "facade.html"
    with open(facade_file, "w", encoding="utf-8") as f:
        f.write(html)


# === Handler (handler.py) ===

def get_panel_handler(panel_id: str) -> Optional[Any]:
    """
    Load panel handler module with caching and hot-reload.
    Returns the module or None if no handler exists.
    """
    handler_file = get_panel_dir(panel_id) / "handler.py"
    if not handler_file.exists():
        return None
    
    mtime = handler_file.stat().st_mtime
    cached = _handler_cache.get(panel_id)
    
    # Return cached if not modified
    if cached and cached[0] == mtime:
        return cached[1]
    
    # Load/reload module
    try:
        spec = importlib.util.spec_from_file_location(
            f"panel_handler_{panel_id}", 
            handler_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        _handler_cache[panel_id] = (mtime, module)
        return module
    except Exception as e:
        print(f"[ERROR] Failed to load handler for {panel_id}: {e}")
        return None


def save_panel_handler(panel_id: str, code: str) -> None:
    """Save panel handler.py."""
    panel_dir = get_panel_dir(panel_id)
    panel_dir.mkdir(parents=True, exist_ok=True)
    
    handler_file = panel_dir / "handler.py"
    with open(handler_file, "w", encoding="utf-8") as f:
        f.write(code)
    
    # Invalidate cache
    if panel_id in _handler_cache:
        del _handler_cache[panel_id]


async def invoke_handler(panel_id: str, action: str, payload: dict) -> Optional[dict]:
    """
    Invoke panel handler's handle_action function.
    
    Handler should export:
        async def handle_action(action: str, payload: dict, data: dict) -> dict
    
    Returns updated data, or None if no handler or error.
    """
    handler = get_panel_handler(panel_id)
    if handler is None:
        return None
    
    if not hasattr(handler, "handle_action"):
        return None
    
    data = get_panel_data(panel_id) or {}
    
    try:
        handle_fn = handler.handle_action
        # Support both sync and async handlers
        import asyncio
        if asyncio.iscoroutinefunction(handle_fn):
            result = await handle_fn(action, payload, data)
        else:
            result = handle_fn(action, payload, data)
        
        if result is not None:
            save_panel_data(panel_id, result)
            return result
    except Exception as e:
        print(f"[ERROR] Handler error for {panel_id}.{action}: {e}")
        return None
    
    return data


# === Panel CRUD ===

def create_panel(
    panel_type: str,
    title: str,
    facade_html: str,
    data: Optional[dict] = None,
    handler_code: Optional[str] = None,
    panel_id: Optional[str] = None,
) -> str:
    """
    Create a new panel with all its resources.
    Returns the panel ID.
    """
    ensure_panels_dir()
    
    if panel_id is None:
        panel_id = generate_panel_id(panel_type)
    
    panel_dir = get_panel_dir(panel_id)
    panel_dir.mkdir(parents=True, exist_ok=True)
    
    # Save data.json
    panel_data = data or {}
    panel_data["id"] = panel_id
    panel_data["type"] = panel_type
    panel_data["title"] = title
    panel_data["createdAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    save_panel_data(panel_id, panel_data)
    
    # Save facade.html
    save_panel_facade(panel_id, facade_html)
    
    # Save handler.py (optional)
    if handler_code:
        save_panel_handler(panel_id, handler_code)
    
    return panel_id


def delete_panel(panel_id: str) -> bool:
    """Delete a panel and all its resources."""
    panel_dir = get_panel_dir(panel_id)
    if not panel_dir.exists():
        return False
    
    import shutil
    shutil.rmtree(panel_dir)
    
    # Clear handler cache
    if panel_id in _handler_cache:
        del _handler_cache[panel_id]
    
    return True


def get_panel(panel_id: str) -> Optional[dict]:
    """
    Get full panel info (data + facade).
    """
    data = get_panel_data(panel_id)
    if data is None:
        return None
    
    facade = get_panel_facade(panel_id)
    handler_exists = (get_panel_dir(panel_id) / "handler.py").exists()
    
    return {
        **data,
        "facade": facade,
        "hasHandler": handler_exists,
    }
