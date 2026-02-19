"""Cards API routes for dashboard management."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional, List
from datetime import datetime, timezone
import uuid
import json

from app.services.dashboard import get_dashboard, save_dashboard
from app.services.snapshots import create_snapshot, get_changelog, get_snapshot

router = APIRouter(prefix="/api/cards", tags=["cards"])


class CreateCardRequest(BaseModel):
    type: str
    title: str
    content: Any
    size: str = "3x2"  # Grid size "WxH"
    position: Optional[dict] = None  # {x, y} grid position
    titleColor: Optional[str] = None
    titleClass: Optional[str] = None


class UpdateCardRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[Any] = None
    size: Optional[str] = None  # Grid size like "3x2"
    position: Optional[dict] = None  # {x: col, y: row} grid position
    type: Optional[str] = None
    titleColor: Optional[str] = None
    titleClass: Optional[str] = None


class ReorderCardsRequest(BaseModel):
    cardIds: List[str]  # Cards in desired order


class MergeCardsRequest(BaseModel):
    cardIds: List[str]
    title: str


@router.get("")
async def list_cards():
    """List all cards on the dashboard."""
    dashboard = get_dashboard()
    return dashboard.get("cards", [])


@router.get("/{card_id}")
async def get_card(card_id: str):
    """Get a specific card by ID."""
    dashboard = get_dashboard()
    for card in dashboard.get("cards", []):
        if card["id"] == card_id:
            return card
    raise HTTPException(status_code=404, detail="Card not found")


# Default minimum sizes per card type
DEFAULT_MIN_SIZES = {
    'weather': (3, 2),
    'todo': (2, 2),
    'news-single': (3, 2),
    'news-bundle': (4, 3),
    'crypto': (2, 2),
    'crypto-bundle': (3, 3),
    'reminder': (2, 2),
    'countdown': (2, 2),
    'chat': (4, 3),
}

def enforce_min_size(card_type: str, size: str, content: dict = None) -> str:
    """Ensure size meets minimum for card type. Card can override via content.minSize."""
    # Check card's own minSize first
    if content and isinstance(content, dict) and content.get('minSize'):
        min_size_str = content['minSize']
        if 'x' in min_size_str:
            parts = min_size_str.split('x')
            min_w, min_h = int(parts[0]), int(parts[1])
        else:
            min_w, min_h = 2, 2
    else:
        min_w, min_h = DEFAULT_MIN_SIZES.get(card_type, (2, 2))
    
    if 'x' in size:
        parts = size.split('x')
        w = int(parts[0])
        h = int(parts[1])
    else:
        # Legacy size
        return size
    
    w = max(w, min_w)
    h = max(h, min_h)
    return f"{w}x{h}"


@router.post("")
async def create_card(request: CreateCardRequest):
    """Create a new card."""
    dashboard = get_dashboard()
    
    # Generate ID based on type
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d%H%M%S")
    card_id = f"{request.type}-{timestamp}-{uuid.uuid4().hex[:4]}"
    
    # Normalize content - parse JSON string if needed
    content = request.content
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except json.JSONDecodeError:
            pass
    
    # Enforce minimum size for card type (content may have minSize)
    size = enforce_min_size(request.type, request.size, content)
    
    # Position: use provided or find next available spot
    position = request.position
    if not position:
        # Find a free spot (simple: stack vertically)
        existing_cards = dashboard.get("cards", [])
        max_y = 0
        for c in existing_cards:
            pos = c.get("position", {})
            card_size = c.get("size", "3x2")
            if "x" in card_size:
                h = int(card_size.split("x")[1])
            else:
                h = 2
            card_bottom = pos.get("y", 0) + h
            if card_bottom > max_y:
                max_y = card_bottom
        position = {"x": 0, "y": max_y}
    
    new_card = {
        "id": card_id,
        "type": request.type,
        "title": request.title,
        "content": content,
        "position": position,
        "size": size,
        "createdAt": now.isoformat().replace("+00:00", "Z"),
        "updatedAt": now.isoformat().replace("+00:00", "Z"),
    }
    
    # Optional title styling
    if request.titleColor:
        new_card["titleColor"] = request.titleColor
    if request.titleClass:
        new_card["titleClass"] = request.titleClass
    
    dashboard.setdefault("cards", []).append(new_card)
    dashboard["updatedAt"] = now.isoformat().replace("+00:00", "Z")
    save_dashboard(dashboard)
    
    # Create snapshot
    create_snapshot(
        dashboard, 
        action="create",
        details=f"Created {request.type} card: {request.title}",
        card_id=card_id
    )
    
    return new_card


@router.patch("/{card_id}")
async def update_card(card_id: str, request: UpdateCardRequest):
    """Update an existing card."""
    dashboard = get_dashboard()
    
    for card in dashboard.get("cards", []):
        if card["id"] == card_id:
            now = datetime.now(timezone.utc)
            old_title = card.get("title")
            
            if request.title is not None:
                card["title"] = request.title
            if request.content is not None:
                # Merge content instead of replace
                if isinstance(card.get("content"), dict) and isinstance(request.content, dict):
                    card["content"].update(request.content)
                else:
                    card["content"] = request.content
            if request.size is not None:
                card["size"] = enforce_min_size(card.get("type", ""), request.size, card.get("content"))
            if request.type is not None:
                card["type"] = request.type
            if request.position is not None:
                card["position"] = request.position  # {x, y} grid coordinates
            if request.titleColor is not None:
                card["titleColor"] = request.titleColor
            if request.titleClass is not None:
                card["titleClass"] = request.titleClass
            
            card["updatedAt"] = now.isoformat().replace("+00:00", "Z")
            dashboard["updatedAt"] = now.isoformat().replace("+00:00", "Z")
            
            save_dashboard(dashboard)
            
            # Create snapshot
            create_snapshot(
                dashboard,
                action="update", 
                details=f"Updated card: {card.get('title', old_title)}",
                card_id=card_id
            )
            
            return card
    
    raise HTTPException(status_code=404, detail="Card not found")


@router.delete("/{card_id}")
async def delete_card(card_id: str):
    """Delete a card."""
    dashboard = get_dashboard()
    
    cards = dashboard.get("cards", [])
    deleted_card = None
    for c in cards:
        if c["id"] == card_id:
            deleted_card = c
            break
    
    if not deleted_card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    dashboard["cards"] = [c for c in cards if c["id"] != card_id]
    
    now = datetime.now(timezone.utc)
    dashboard["updatedAt"] = now.isoformat().replace("+00:00", "Z")
    save_dashboard(dashboard)
    
    # Create snapshot
    create_snapshot(
        dashboard,
        action="delete",
        details=f"Deleted card: {deleted_card.get('title')} ({deleted_card.get('type')})",
        card_id=card_id
    )
    
    return {"deleted": card_id}


@router.post("/reorder")
async def reorder_cards(request: ReorderCardsRequest):
    """Reorder cards by providing the card IDs in desired order."""
    dashboard = get_dashboard()
    cards = dashboard.get("cards", [])
    
    # Create a map of cards by ID
    card_map = {c["id"]: c for c in cards}
    
    # Validate all IDs exist
    for card_id in request.cardIds:
        if card_id not in card_map:
            raise HTTPException(status_code=404, detail=f"Card not found: {card_id}")
    
    # Update positions
    now = datetime.now(timezone.utc)
    for i, card_id in enumerate(request.cardIds):
        card_map[card_id]["position"] = {"order": i}
        card_map[card_id]["updatedAt"] = now.isoformat().replace("+00:00", "Z")
    
    # Sort cards by new positions
    dashboard["cards"].sort(key=lambda c: c.get("position", {}).get("order", 999))
    dashboard["updatedAt"] = now.isoformat().replace("+00:00", "Z")
    save_dashboard(dashboard)
    
    # Create snapshot
    create_snapshot(
        dashboard,
        action="reorder",
        details=f"Reordered {len(request.cardIds)} cards",
        card_id=None
    )
    
    return {"reordered": request.cardIds}


@router.post("/merge")
async def merge_cards(request: MergeCardsRequest):
    """Merge multiple cards into a bundle."""
    dashboard = get_dashboard()
    cards = dashboard.get("cards", [])
    
    # Find cards to merge
    to_merge = []
    remaining = []
    for card in cards:
        if card["id"] in request.cardIds:
            to_merge.append(card)
        else:
            remaining.append(card)
    
    if len(to_merge) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 cards to merge")
    
    # Check all cards are same type
    types = set(c["type"] for c in to_merge)
    if len(types) > 1:
        # Allow merging single types into bundles
        base_types = set(t.replace("-bundle", "").replace("-single", "") for t in types)
        if len(base_types) > 1:
            raise HTTPException(status_code=400, detail=f"Cannot merge different types: {types}")
    
    # Determine merged type
    first_type = to_merge[0]["type"]
    if first_type in ("crypto", "crypto-bundle"):
        merged_type = "crypto-bundle"
    elif first_type in ("news-single", "news-bundle"):
        merged_type = "news-bundle"
    else:
        raise HTTPException(status_code=400, detail=f"Cannot merge type: {first_type}")
    
    # Collect items
    items = []
    merged_titles = []
    for card in to_merge:
        merged_titles.append(card.get("title", card["id"]))
        content = card.get("content", {})
        if "items" in content:
            items.extend(content["items"])
        else:
            # Single item card
            items.append(content)
    
    # Create merged card
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d%H%M%S")
    merged_card = {
        "id": f"{merged_type}-{timestamp}-{uuid.uuid4().hex[:4]}",
        "type": merged_type,
        "title": request.title,
        "content": {"items": items},
        "position": {"order": min(c.get("position", {}).get("order", 999) for c in to_merge)},
        "size": "medium",
        "createdAt": now.isoformat().replace("+00:00", "Z"),
        "updatedAt": now.isoformat().replace("+00:00", "Z"),
    }
    
    # Update dashboard
    remaining.append(merged_card)
    dashboard["cards"] = remaining
    dashboard["updatedAt"] = now.isoformat().replace("+00:00", "Z")
    save_dashboard(dashboard)
    
    # Create snapshot
    create_snapshot(
        dashboard,
        action="merge",
        details=f"Merged {len(to_merge)} cards into: {request.title}",
        card_id=merged_card["id"]
    )
    
    return merged_card
