from scheduler.decorators import scheduled
import httpx
from datetime import datetime

@scheduled("0 * * * *")
async def refresh_weather(data: dict) -> dict:
    """每小时刷新天气数据"""
    
    lat = data.get("latitude", 1.29)
    lon = data.get("longitude", 103.85)
    
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                "current": "temperature_2m,weather_code",
                "timezone": "auto",
                "forecast_days": 7
            }
        )
        resp.raise_for_status()
        weather = resp.json()
    
    def get_icon(code):
        if code in [95, 96, 99]: return "⛈️"
        elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]: return "🌧️"
        elif code in [71, 73, 75, 77, 85, 86]: return "🌨️"
        elif code == 0: return "☀️"
        elif code in [1, 2]: return "🌤️"
        elif code in [3, 45, 48]: return "☁️"
        else: return "🌤️"
    
    def get_cn(code):
        if code in [95, 96, 99]: return "雷阵雨"
        elif code in [80, 81, 82]: return "阵雨"
        elif code in [61, 63, 65, 66, 67]: return "雨"
        elif code in [51, 53, 55, 56, 57]: return "小雨"
        elif code in [71, 73, 75, 77, 85, 86]: return "雪"
        elif code == 0: return "晴"
        elif code in [1, 2]: return "多云"
        elif code == 3: return "阴"
        elif code in [45, 48]: return "雾"
        else: return "多云"
    
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    daily = weather["daily"]
    current = weather["current"]
    
    days = []
    for i in range(len(daily["time"])):
        date = datetime.strptime(daily["time"][i], "%Y-%m-%d")
        day_name = "今天" if i == 0 else weekdays[date.weekday()]
        code = daily["weather_code"][i]
        days.append({
            "day": day_name,
            "icon": get_icon(code),
            "high": int(daily["temperature_2m_max"][i]),
            "low": int(daily["temperature_2m_min"][i]),
            "condition": get_cn(code)
        })
    
    data["temperature"] = f"{int(current['temperature_2m'])}°C"
    data["condition"] = get_cn(current["weather_code"])
    data["days"] = days
    
    return data
