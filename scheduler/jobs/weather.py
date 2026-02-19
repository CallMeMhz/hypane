#!/usr/bin/env python3
"""
天气更新脚本

使用 wttr.in API 获取天气信息（免费，无需 API key）
"""

import json
import httpx
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
DASHBOARD_FILE = BASE_DIR / "data" / "dashboard.json"

# 默认城市，可通过环境变量 WEATHER_CITY 覆盖
import os
CITY = os.environ.get("WEATHER_CITY", "Shanghai")


def get_weather(city: str) -> dict:
    """从 wttr.in 获取天气"""
    url = f"https://wttr.in/{city}?format=j1"
    
    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data["current_condition"][0]
        weather = data.get("weather", [{}])[0]
        
        return {
            "location": city,
            "temperature": f"{current['temp_C']}°C",
            "condition": current["weatherDesc"][0]["value"],
            "forecast": f"今日最高 {weather.get('maxtempC', 'N/A')}°C，最低 {weather.get('mintempC', 'N/A')}°C",
        }
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None


def update_dashboard(weather_data: dict):
    """更新 dashboard.json 中的天气卡片"""
    if not DASHBOARD_FILE.exists():
        print("Dashboard file not found")
        return
    
    with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
        dashboard = json.load(f)
    
    # 查找或创建天气卡片
    weather_card = None
    for card in dashboard.get("cards", []):
        if card.get("type") == "weather":
            weather_card = card
            break
    
    now = datetime.now().isoformat()
    
    if weather_card:
        weather_card["content"] = weather_data
        weather_card["updatedAt"] = now
    else:
        # 创建新卡片
        max_order = max((c.get("position", {}).get("order", 0) for c in dashboard.get("cards", [])), default=0)
        dashboard.setdefault("cards", []).insert(0, {
            "id": "weather-001",
            "type": "weather",
            "title": "今日天气",
            "content": weather_data,
            "position": {"order": max_order + 1},
            "size": "small",
            "createdAt": now,
            "updatedAt": now,
        })
    
    dashboard["updatedAt"] = now
    
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)
    
    print(f"Weather updated: {weather_data['location']} - {weather_data['temperature']}")


def main():
    weather = get_weather(CITY)
    if weather:
        update_dashboard(weather)


if __name__ == "__main__":
    main()
