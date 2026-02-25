"""Sandbox protocol - defines handler interface."""

from dataclasses import dataclass
from typing import Any, Callable
from enum import Enum


class EventType(Enum):
    ACTION = "action"      # User interaction from frontend
    SCHEDULE = "schedule"  # Scheduled task execution
    INIT = "init"          # Panel installation (first-time setup)


@dataclass
class HandlerEvent:
    """Event passed to handler."""
    type: EventType
    action: str | None = None   # For ACTION type
    payload: dict | None = None  # For ACTION type


@dataclass
class HandlerContext:
    """Context passed to handler execution."""
    panel_id: str | None = None  # Panel ID (if panel handler)
    task_id: str | None = None   # Task ID (if task handler)
    storage: dict[str, dict] = None  # {storage_id: data}
    event: HandlerEvent = None


@dataclass 
class HandlerResult:
    """Result from handler execution."""
    success: bool
    error: str | None = None
    # Storage is modified in-place, no need to return


# Handler function signatures:
# def on_init(storage: dict) -> None      # Called once at panel installation
# def on_action(action: str, payload: dict, storage: dict) -> None
# def on_schedule(storage: dict) -> None
