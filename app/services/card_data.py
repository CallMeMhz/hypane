"""
卡片数据 Provider

为卡片渲染提供实时数据，从 history 读取或直接调 API
"""

from typing import Any, Optional
from app.services.history import read_latest


def get_card_data(card: dict) -> Optional[dict]:
    """
    获取卡片的实时数据
    
    Args:
        card: 卡片配置
    
    Returns:
        合并了实时数据的 content，或 None 表示使用原始 content
    """
    card_type = card.get("type")
    content = card.get("content", {})
    
    if card_type == "weather":
        return _get_weather_data(content)
    elif card_type in ("crypto", "crypto-bundle"):
        return _get_crypto_data(content)
    
    # 其他类型返回 None，使用原始 content
    return None


def _get_weather_data(content: dict) -> Optional[dict]:
    """获取天气数据"""
    location = content.get("location", "Singapore")
    
    # 从历史读取
    data = read_latest(f"weather/{location.lower()}")
    if data:
        return {
            "location": data.get("location", location),
            "temperature": f"{data['temperature']}°C",
            "condition": data.get("condition", ""),
            "forecast": f"最高 {data.get('maxTemp', 'N/A')}°C，最低 {data.get('minTemp', 'N/A')}°C",
        }
    
    return None


def _get_crypto_data(content: dict) -> Optional[dict]:
    """获取加密货币数据"""
    # 从历史读取
    data = read_latest("crypto")
    if not data:
        return None
    
    # 如果是 bundle，更新 items
    if "items" in content:
        items = []
        for item in content["items"]:
            symbol = item.get("symbol")
            if symbol and symbol in data:
                items.append({
                    **item,
                    "price": f"{data[symbol]['price']:,.2f}",
                    "change": data[symbol].get("change24h", 0),
                })
            else:
                items.append(item)
        return {"items": items}
    
    return None
