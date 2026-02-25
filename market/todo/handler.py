"""Todo panel handler."""


def on_action(action: str, payload: dict, storage: dict) -> None:
    todo = storage.get("todo", {})
    items = todo.get("items", [])
    
    if action == "add":
        text = payload.get("text", "").strip()
        if text:
            items.append({
                "id": hex(int(time.time() * 1000))[2:],
                "text": text,
                "done": False
            })
            todo["items"] = items
    
    elif action == "toggle":
        item_id = payload.get("id")
        for item in items:
            if item["id"] == item_id:
                item["done"] = not item["done"]
                break
    
    elif action == "remove":
        item_id = payload.get("id")
        todo["items"] = [i for i in items if i["id"] != item_id]
