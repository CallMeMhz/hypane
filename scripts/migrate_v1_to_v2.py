#!/usr/bin/env python3
"""Migrate dashboard.json v1 (cards) to v2 (panels)."""

import json
import shutil
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")
DASHBOARD_FILE = DATA_DIR / "dashboard.json"
PANELS_DIR = DATA_DIR / "panels"


def migrate():
    if not DASHBOARD_FILE.exists():
        print("No dashboard.json found, nothing to migrate.")
        return
    
    with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Check if already migrated
    if data.get("version", 1) == 2:
        print("Already migrated to v2.")
        return
    
    # Backup
    backup_file = DASHBOARD_FILE.with_suffix(".json.v1.backup")
    shutil.copy(DASHBOARD_FILE, backup_file)
    print(f"Backed up to {backup_file}")
    
    cards = data.get("cards", [])
    print(f"Migrating {len(cards)} cards to panels...")
    
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    
    layout_panels = []
    
    for card in cards:
        card_id = card.get("id")
        if not card_id:
            continue
        
        panel_dir = PANELS_DIR / card_id
        panel_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract content
        content = card.get("content", {})
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except:
                content = {"raw": content}
        
        # Extract HTML facade
        facade_html = ""
        if isinstance(content, dict):
            facade_html = content.pop("html", "")
        
        # Build data.json
        panel_data = {
            "id": card_id,
            "type": card.get("type", "custom"),
            "title": card.get("title", "Untitled"),
            "createdAt": card.get("createdAt"),
            "updatedAt": card.get("updatedAt"),
        }
        
        # Merge remaining content into data
        if isinstance(content, dict):
            for key, value in content.items():
                if key not in panel_data:
                    panel_data[key] = value
        
        # Handle minSize
        if isinstance(content, dict) and "minSize" in content:
            panel_data["minSize"] = content["minSize"]
        
        # Save data.json
        data_file = panel_dir / "data.json"
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(panel_data, f, ensure_ascii=False, indent=2)
        
        # Save facade.html
        if facade_html:
            facade_file = panel_dir / "facade.html"
            with open(facade_file, "w", encoding="utf-8") as f:
                f.write(facade_html)
        
        # Add to layout
        layout_panels.append({
            "id": card_id,
            "position": card.get("position", {"x": 0, "y": 0}),
            "size": card.get("size", "3x2"),
        })
        
        print(f"  ✓ {card_id}")
    
    # Save new dashboard.json (layout only)
    new_dashboard = {
        "version": 2,
        "panels": layout_panels,
        "userPreferences": data.get("userPreferences", {}),
    }
    
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(new_dashboard, f, ensure_ascii=False, indent=2)
    
    print(f"\nMigration complete! {len(layout_panels)} panels created.")
    print(f"Panels directory: {PANELS_DIR}")


if __name__ == "__main__":
    migrate()
