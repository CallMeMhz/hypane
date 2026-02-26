"""Hacker News panel handler - fetch top stories from HN Firebase API."""
from datetime import datetime

import httpx

HN_API = "https://hacker-news.firebaseio.com/v0"


def on_init(storage: dict) -> None:
    """Called once when panel is installed."""
    _refresh(storage)


def on_action(action: str, payload: dict, storage: dict) -> None:
    """Handle panel actions."""
    if action == "refresh":
        _refresh(storage)


def on_schedule(storage: dict) -> None:
    """Scheduled refresh (called by task scheduler)."""
    _refresh(storage)


def _utcnow():
    """Get current UTC time as naive datetime."""
    return datetime.utcnow()


def _time_ago(ts: int) -> str:
    """Convert unix timestamp to relative time string."""
    delta = _utcnow() - datetime.utcfromtimestamp(ts)
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def _domain(url: str) -> str:
    """Extract domain from URL using string ops."""
    if not url:
        return ""
    try:
        # Remove scheme
        s = url.split("://", 1)[-1]
        # Take host part
        host = s.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
        # Remove port
        host = host.rsplit(":", 1)[0]
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def _strip_html(text: str) -> str:
    """Strip HTML tags using simple state machine."""
    result = []
    in_tag = False
    for ch in text:
        if ch == "<":
            in_tag = True
            result.append(" ")
        elif ch == ">":
            in_tag = False
        elif not in_tag:
            result.append(ch)
    # Collapse whitespace
    return " ".join("".join(result).split())


def _refresh(storage: dict) -> None:
    """Fetch top stories and top comments from HN."""
    hn = storage.get("hackernews", {})

    with httpx.Client(timeout=30) as client:
        resp = client.get(f"{HN_API}/topstories.json")
        resp.raise_for_status()
        top_ids = resp.json()[:15]

        stories = []
        for story_id in top_ids:
            try:
                item_resp = client.get(f"{HN_API}/item/{story_id}.json")
                item_resp.raise_for_status()
                item = item_resp.json()
                if not item or item.get("type") != "story":
                    continue

                url = item.get("url", "")
                story = {
                    "title": item.get("title", ""),
                    "url": url,
                    "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
                    "score": item.get("score", 0),
                    "by": item.get("by", ""),
                    "comments_count": item.get("descendants", 0),
                    "time_ago": _time_ago(item.get("time", 0)),
                    "domain": _domain(url),
                    "top_comment": None,
                }

                kids = item.get("kids", [])
                if kids:
                    try:
                        c_resp = client.get(f"{HN_API}/item/{kids[0]}.json")
                        c_resp.raise_for_status()
                        comment = c_resp.json()
                        if comment and comment.get("text"):
                            text = _strip_html(comment["text"])
                            if len(text) > 200:
                                text = text[:200] + "..."
                            story["top_comment"] = {
                                "by": comment.get("by", ""),
                                "text": text,
                            }
                    except Exception:
                        pass

                stories.append(story)
            except Exception:
                continue

    hn["stories"] = stories
    hn["updated_at"] = _utcnow().isoformat()
