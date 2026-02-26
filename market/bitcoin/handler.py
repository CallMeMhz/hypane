"""Bitcoin price panel handler - fetch BTC/USDT from Binance public API."""
from datetime import datetime

import httpx

TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
KLINES_URL = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=24"


def on_init(storage: dict) -> None:
    _refresh(storage)


def on_action(action: str, payload: dict, storage: dict) -> None:
    if action == "refresh":
        _refresh(storage)


def on_schedule(storage: dict) -> None:
    _refresh(storage)


def _fmt_volume(v: float) -> str:
    """Format volume to human-readable string."""
    if v >= 1_000_000_000:
        return f"${v / 1_000_000_000:.1f}B"
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    return f"${v:,.0f}"


def _refresh(storage: dict) -> None:
    btc = storage.get("bitcoin", {})

    with httpx.Client(timeout=15) as client:
        # 24h ticker
        resp = client.get(TICKER_URL)
        resp.raise_for_status()
        ticker = resp.json()

        btc["price"] = float(ticker["lastPrice"])
        btc["change_24h"] = float(ticker["priceChangePercent"])
        btc["high_24h"] = float(ticker["highPrice"])
        btc["low_24h"] = float(ticker["lowPrice"])
        btc["volume"] = _fmt_volume(float(ticker["quoteVolume"]))

        # 24h hourly klines for sparkline
        resp = client.get(KLINES_URL)
        resp.raise_for_status()
        klines = resp.json()
        # Each kline: [open_time, open, high, low, close, ...]
        btc["sparkline"] = [float(k[4]) for k in klines]

    btc["updated_at"] = datetime.utcnow().isoformat()
