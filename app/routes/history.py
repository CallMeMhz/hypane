"""Changelog and Snapshots API routes."""

from fastapi import APIRouter, HTTPException, Query

from app.services.snapshots import get_changelog, get_snapshot

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
