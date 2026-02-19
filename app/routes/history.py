"""Changelog, Snapshots and History API routes."""

from fastapi import APIRouter, HTTPException, Query

from app.services.snapshots import get_changelog, get_snapshot
from app.services.history import read_history, list_sources

router = APIRouter(tags=["history"])


@router.get("/api/changelog")
async def api_get_changelog(limit: int = Query(default=20, le=100)):
    """Get recent changelog entries."""
    return get_changelog(limit)


@router.get("/api/snapshots/{snapshot_id}")
async def api_get_snapshot(snapshot_id: str):
    """Get a specific snapshot."""
    snapshot = get_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snapshot


@router.get("/api/history")
async def api_list_history_sources():
    """List available history data sources."""
    return list_sources()


@router.get("/api/history/{source:path}")
async def api_get_history(source: str, range: str = Query(default="7d")):
    """Get historical data for a source."""
    records = read_history(source, range)
    return records
