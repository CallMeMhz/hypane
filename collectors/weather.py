"""
天气数据采集器

使用 wttr.in API（免费，无需 key）
"""

import httpx
from typing import Optional

# 添加项目根目录到 path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.history import write_history


def fetch_weather(location: str) -> Optional[dict]:
    """从 wttr.in 获取天气数据"""
    url = f"https://wttr.in/{location}?format=j1"
    
    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data["current_condition"][0]
        weather = data.get("weather", [{}])[0]
        
        return {
            "location": location,
            "temperature": int(current["temp_C"]),
            "feelsLike": int(current["FeelsLikeC"]),
            "condition": current["weatherDesc"][0]["value"],
            "humidity": int(current["humidity"]),
            "windSpeed": int(current["windspeedKmph"]),
            "maxTemp": int(weather.get("maxtempC", 0)),
            "minTemp": int(weather.get("mintempC", 0)),
        }
    except Exception as e:
        print(f"Error fetching weather for {location}: {e}")
        return None


def collect(locations: list[str] = None):
    """
    采集天气数据并写入历史
    
    Args:
        locations: 城市列表，默认 ["Singapore"]
    """
    if locations is None:
        locations = ["Singapore"]
    
    for loc in locations:
        data = fetch_weather(loc)
        if data:
            # 按天存储，用 location 作为 key
            write_history(
                source=f"weather/{loc.lower()}",
                data=data,
                granularity="day"
            )
            print(f"Collected weather for {loc}: {data['temperature']}°C")


if __name__ == "__main__":
    collect()
