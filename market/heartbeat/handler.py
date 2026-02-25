"""Heartbeat panel handler - increments a counter every 5 seconds."""
from datetime import datetime


def on_init(storage: dict) -> None:
    """Initialize heartbeat data."""
    hb = storage.get("heartbeat", {})
    now = datetime.now().isoformat()
    hb["beat"] = 0
    hb["started_at"] = now
    hb["last_beat"] = now


def on_schedule(storage: dict) -> None:
    """Scheduled tick - increment counter."""
    hb = storage.get("heartbeat", {})
    hb["beat"] = hb.get("beat", 0) + 1
    hb["last_beat"] = datetime.now().isoformat()
