"""Panel tools - tools for AI agent to manipulate panels and storages."""

import json
from datetime import datetime

from .base import ToolDefinition


# Tool definitions for panel management
PANEL_TOOLS = [
    ToolDefinition(
        name="create_storage",
        description="Create a new storage (JSON data container) that can be shared between panels and tasks.",
        parameters={
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Unique storage ID (use lowercase with hyphens, e.g., 'my-todos')"
                },
                "data": {
                    "type": "object",
                    "description": "Initial data for the storage"
                }
            },
            "required": ["id"]
        }
    ),
    ToolDefinition(
        name="update_storage",
        description="Update data in an existing storage.",
        parameters={
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Storage ID to update"
                },
                "data": {
                    "type": "object",
                    "description": "New data to merge/replace"
                },
                "replace": {
                    "type": "boolean",
                    "description": "If true, replace all data. If false, merge with existing.",
                    "default": False
                }
            },
            "required": ["id", "data"]
        }
    ),
    ToolDefinition(
        name="create_panel",
        description="Create a new dashboard panel with template and optional handler.",
        parameters={
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Unique panel ID"
                },
                "title": {
                    "type": "string",
                    "description": "Panel title displayed in header"
                },
                "icon": {
                    "type": "string",
                    "description": "Lucide icon name (e.g., 'check-square', 'cloud', 'list')"
                },
                "desc": {
                    "type": "string",
                    "description": "Description of what this panel does (for AI reference)"
                },
                "size": {
                    "type": "string",
                    "description": "Panel size as WxH (e.g., '3x2', '4x3')"
                },
                "storage_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IDs of storages this panel can access"
                },
                "template": {
                    "type": "string",
                    "description": "Jinja2 HTML template for rendering the panel"
                },
                "handler": {
                    "type": "string",
                    "description": "Python handler code with on_action(action, payload, storage) function"
                }
            },
            "required": ["id", "title"]
        }
    ),
    ToolDefinition(
        name="update_panel_template",
        description="Update a panel's Jinja2 template.",
        parameters={
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Panel ID"
                },
                "template": {
                    "type": "string",
                    "description": "New Jinja2 HTML template"
                }
            },
            "required": ["id", "template"]
        }
    ),
    ToolDefinition(
        name="update_panel_handler",
        description="Update a panel's Python handler code.",
        parameters={
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Panel ID"
                },
                "handler": {
                    "type": "string",
                    "description": "Python handler code with on_action function"
                }
            },
            "required": ["id", "handler"]
        }
    ),
    ToolDefinition(
        name="create_task",
        description="Create a scheduled task that runs periodically.",
        parameters={
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Unique task ID"
                },
                "name": {
                    "type": "string",
                    "description": "Task name"
                },
                "schedule": {
                    "type": "string",
                    "description": "Cron expression (minute hour day month weekday), e.g., '0 * * * *' for hourly"
                },
                "storage_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IDs of storages this task can access"
                },
                "handler": {
                    "type": "string",
                    "description": "Python handler code with on_schedule(storage) function"
                }
            },
            "required": ["id", "name", "schedule"]
        }
    ),
]


async def execute_panel_tool(tool_name: str, args: dict) -> str:
    """Execute a panel tool and return result."""
    from app.services import storage as storage_service
    from app.services import panels_v2 as panel_service
    from app.services import tasks_v2 as task_service
    from app.models.panel import Panel
    from app.models.task import Task
    
    try:
        if tool_name == "create_storage":
            result = storage_service.create_storage(args["id"], args.get("data", {}))
            return f"Created storage '{args['id']}'"
        
        elif tool_name == "update_storage":
            if args.get("replace"):
                result = storage_service.update_storage(args["id"], args["data"])
            else:
                result = storage_service.patch_storage(args["id"], args["data"])
            if result:
                return f"Updated storage '{args['id']}'"
            return f"Storage '{args['id']}' not found"
        
        elif tool_name == "create_panel":
            result = panel_service.create_panel(
                panel_id=args["id"],
                title=args.get("title", "Untitled"),
                icon=args.get("icon", "cube"),
                desc=args.get("desc", ""),
                size=args.get("size", "3x2"),
                storage_ids=args.get("storage_ids", []),
                template=args.get("template", ""),
                handler=args.get("handler", ""),
            )
            return f"Created panel '{args['id']}'"
        
        elif tool_name == "update_panel_template":
            panel = Panel.load(args["id"])
            if not panel:
                return f"Panel '{args['id']}' not found"
            panel.set_template(args["template"])
            return f"Updated template for panel '{args['id']}'"
        
        elif tool_name == "update_panel_handler":
            panel = Panel.load(args["id"])
            if not panel:
                return f"Panel '{args['id']}' not found"
            panel.set_handler(args["handler"])
            return f"Updated handler for panel '{args['id']}'"
        
        elif tool_name == "create_task":
            result = task_service.create_task(
                task_id=args["id"],
                name=args.get("name", "Untitled"),
                schedule=args.get("schedule", ""),
                storage_ids=args.get("storage_ids", []),
                handler=args.get("handler", ""),
            )
            return f"Created task '{args['id']}'"
        
        else:
            return f"Unknown tool: {tool_name}"
            
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"
