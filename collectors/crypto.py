"""
加密货币价格采集器

使用 CoinGecko API（免费，无需 key）
"""

import httpx
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.history import write_history


COIN_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XRP": "ripple",
    "DOGE": "dogecoin",
}


def fetch_prices(symbols: list[str] = None) -> Optional[dict]:
    """从 CoinGecko 获取价格"""
    if symbols is None:
        symbols = ["BTC", "ETH"]
    
    ids = [COIN_IDS.get(s, s.lower()) for s in symbols]
    ids_str = ",".join(ids)
    
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd&include_24hr_change=true"
    
    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = {}
        for symbol in symbols:
            coin_id = COIN_IDS.get(symbol, symbol.lower())
            if coin_id in data:
                result[symbol] = {
                    "price": data[coin_id]["usd"],
                    "change24h": round(data[coin_id].get("usd_24h_change", 0), 2),
                }
        
        return result
    except Exception as e:
        print(f"Error fetching crypto prices: {e}")
        return None


def collect(symbols: list[str] = None):
    """
    采集加密货币价格并写入历史
    
    Args:
        symbols: 币种列表，默认 ["BTC", "ETH"]
    """
    if symbols is None:
        symbols = ["BTC", "ETH"]
    
    data = fetch_prices(symbols)
    if data:
        # 按小时存储
        write_history(
            source="crypto",
            data=data,
            granularity="hour"
        )
        print(f"Collected crypto prices: {data}")


if __name__ == "__main__":
    collect()
