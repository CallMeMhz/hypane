def on_action(action: str, payload: dict, storage: dict) -> None:
    if action == "click":
        cookies = storage.get("cookie-clicker", {})
        amount = payload.get("amount", 1)
        cookies["count"] = cookies.get("count", 0) + amount
