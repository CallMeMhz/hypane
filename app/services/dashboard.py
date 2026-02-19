import json
from typing import Any

from app.config import DASHBOARD_FILE
from app.services.card_data import get_card_data


def _normalize_card(card: dict[str, Any]) -> dict[str, Any]:
    """Normalize card content - parse JSON strings if needed."""
    content = card.get("content")
    if isinstance(content, str):
        try:
            card["content"] = json.loads(content)
        except json.JSONDecodeError:
            pass  # Keep as string if not valid JSON
    return card


def _enrich_card(card: dict[str, Any]) -> dict[str, Any]:
    """Enrich card with live data from providers."""
    live_data = get_card_data(card)
    if live_data:
        # Merge live data into content
        card = card.copy()
        card["content"] = {**card.get("content", {}), **live_data}
    return card


def get_dashboard(enrich: bool = True) -> dict[str, Any]:
    """
    Read dashboard.json and return its content.
    
    Args:
        enrich: If True, enrich cards with live data from providers
    """
    if not DASHBOARD_FILE.exists():
        return {"cards": [], "userPreferences": {}}
    
    with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Normalize all cards
    cards = [_normalize_card(card) for card in data.get("cards", [])]
    
    # Enrich with live data
    if enrich:
        cards = [_enrich_card(card) for card in cards]
    
    data["cards"] = cards
    return data


def save_dashboard(data: dict[str, Any]) -> None:
    """Save data to dashboard.json."""
    DASHBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_card(card_id: str) -> dict[str, Any] | None:
    """Get a single card by ID."""
    dashboard = get_dashboard()
    for card in dashboard.get("cards", []):
        if card.get("id") == card_id:
            return card
    return None


def update_card(card_id: str, updates: dict[str, Any]) -> bool:
    """Update a card by ID."""
    dashboard = get_dashboard()
    for card in dashboard.get("cards", []):
        if card.get("id") == card_id:
            card.update(updates)
            save_dashboard(dashboard)
            return True
    return False


def add_card(card: dict[str, Any]) -> None:
    """Add a new card to dashboard."""
    dashboard = get_dashboard()
    dashboard.setdefault("cards", []).append(card)
    save_dashboard(dashboard)


def delete_card(card_id: str) -> bool:
    """Delete a card by ID."""
    dashboard = get_dashboard()
    cards = dashboard.get("cards", [])
    original_len = len(cards)
    dashboard["cards"] = [c for c in cards if c.get("id") != card_id]
    if len(dashboard["cards"]) < original_len:
        save_dashboard(dashboard)
        return True
    return False
