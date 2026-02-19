"""
Card Actions API - 通用卡片交互路由

每个卡片可以响应 action 请求，更新自己的 content/state。
不同 type 的卡片有不同的 action 处理逻辑。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime, timezone
import uuid

from app.services.dashboard import get_dashboard, save_dashboard

router = APIRouter(prefix="/api/cards", tags=["card-actions"])


class ActionRequest(BaseModel):
    action: str
    payload: Optional[Any] = None


# ============ Action Handlers by Card Type ============

def handle_todo_action(card: dict, action: str, payload: Any) -> dict:
    """Todo 卡片的 action 处理"""
    content = card.get("content", {})
    items = content.get("items", [])
    
    if action == "toggle":
        # payload: { "itemId": "xxx" }
        item_id = payload.get("itemId")
        for item in items:
            if item.get("id") == item_id:
                item["done"] = not item.get("done", False)
                break
    
    elif action == "add":
        # payload: { "text": "xxx", "dueDate": "2026-02-20" }
        new_item = {
            "id": str(uuid.uuid4())[:8],
            "text": payload.get("text", ""),
            "done": False,
        }
        if payload.get("dueDate"):
            new_item["dueDate"] = payload["dueDate"]
        items.append(new_item)
    
    elif action == "delete":
        # payload: { "itemId": "xxx" }
        item_id = payload.get("itemId")
        items = [item for item in items if item.get("id") != item_id]
    
    elif action == "update":
        # payload: { "itemId": "xxx", "text": "new text", "dueDate": "..." }
        item_id = payload.get("itemId")
        for item in items:
            if item.get("id") == item_id:
                if "text" in payload:
                    item["text"] = payload["text"]
                if "dueDate" in payload:
                    item["dueDate"] = payload["dueDate"]
                break
    
    content["items"] = items
    card["content"] = content
    return card


def handle_counter_action(card: dict, action: str, payload: Any) -> dict:
    """计数器类卡片的 action 处理 (cookie-clicker 等)"""
    content = card.get("content", {})
    
    if action == "increment":
        content["count"] = content.get("count", 0) + payload.get("amount", 1)
    elif action == "decrement":
        content["count"] = content.get("count", 0) - payload.get("amount", 1)
    elif action == "set":
        content["count"] = payload.get("value", 0)
    elif action == "reset":
        content["count"] = 0
    
    card["content"] = content
    return card


def handle_generic_action(card: dict, action: str, payload: Any) -> dict:
    """通用 action 处理 - 直接 merge payload 到 content"""
    content = card.get("content", {})
    
    if action == "update" and isinstance(payload, dict):
        content.update(payload)
    elif action == "set" and isinstance(payload, dict):
        card["content"] = payload
    
    card["content"] = content
    return card


# Type -> Handler mapping
ACTION_HANDLERS = {
    "todo": handle_todo_action,
    "cookie-clicker": handle_counter_action,
    "counter": handle_counter_action,
}


@router.post("/{card_id}/action")
async def card_action(card_id: str, request: ActionRequest):
    """
    通用卡片 action 端点
    
    不同 type 的卡片支持不同的 action:
    
    todo:
      - toggle: { itemId } - 切换完成状态
      - add: { text, dueDate? } - 添加项目
      - delete: { itemId } - 删除项目
      - update: { itemId, text?, dueDate? } - 更新项目
    
    cookie-clicker / counter:
      - increment: { amount? } - 增加 (默认 +1)
      - decrement: { amount? } - 减少
      - set: { value } - 设置值
      - reset: {} - 重置为 0
    
    其他类型:
      - update: { ...fields } - merge 到 content
      - set: { ...content } - 替换 content
    """
    dashboard = get_dashboard()
    
    # Find the card
    card = None
    card_index = -1
    for i, c in enumerate(dashboard.get("cards", [])):
        if c["id"] == card_id:
            card = c
            card_index = i
            break
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Get handler for card type
    card_type = card.get("type", "")
    handler = ACTION_HANDLERS.get(card_type, handle_generic_action)
    
    # Execute action
    try:
        updated_card = handler(card, request.action, request.payload or {})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Action failed: {e}")
    
    # Update timestamp and save
    now = datetime.now(timezone.utc)
    updated_card["updatedAt"] = now.isoformat().replace("+00:00", "Z")
    dashboard["cards"][card_index] = updated_card
    dashboard["updatedAt"] = now.isoformat().replace("+00:00", "Z")
    save_dashboard(dashboard)
    
    return {
        "success": True,
        "card": updated_card,
    }


@router.get("/{card_id}/state")
async def get_card_state(card_id: str):
    """获取卡片当前 content (供前端初始化用)"""
    dashboard = get_dashboard()
    
    for card in dashboard.get("cards", []):
        if card["id"] == card_id:
            return {
                "id": card_id,
                "type": card.get("type"),
                "content": card.get("content", {}),
            }
    
    raise HTTPException(status_code=404, detail="Card not found")
