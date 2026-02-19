"""
Hacker News 采集器

使用官方 API 获取热帖
"""

import httpx
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.history import write_history


HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"


def fetch_item(item_id: int) -> Optional[dict]:
    """获取单条内容"""
    try:
        res = httpx.get(HN_ITEM_URL.format(item_id), timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception:
        return None


def fetch_top_stories(limit: int = 20) -> list[dict]:
    """获取热帖列表"""
    try:
        res = httpx.get(HN_TOP_URL, timeout=10)
        res.raise_for_status()
        ids = res.json()[:limit]
        
        stories = []
        for item_id in ids:
            item = fetch_item(item_id)
            if item and item.get("type") == "story":
                stories.append({
                    "id": item["id"],
                    "title": item.get("title", ""),
                    "url": item.get("url", f"https://news.ycombinator.com/item?id={item['id']}"),
                    "score": item.get("score", 0),
                    "comments": item.get("descendants", 0),
                    "by": item.get("by", ""),
                    "time": item.get("time", 0),
                })
        
        return stories
    except Exception as e:
        print(f"Error fetching HN: {e}")
        return []


def collect(limit: int = 20):
    """
    采集 Hacker News 热帖并写入历史
    """
    stories = fetch_top_stories(limit)
    if stories:
        write_history(
            source="hackernews",
            data={"stories": stories},
            granularity="hour"
        )
        print(f"Collected {len(stories)} HN stories")


if __name__ == "__main__":
    collect()
