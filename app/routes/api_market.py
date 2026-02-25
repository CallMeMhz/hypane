"""Panel Market API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.market import (
    list_market_panels,
    get_market_panel,
    search_market,
    install_market_panel,
)
from app.services.dashboard import add_panel_to_layout

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("")
async def list_panels():
    """列出所有市场 Panel 模板"""
    return list_market_panels()


@router.get("/search")
async def search_panels(q: str):
    """搜索市场 Panel"""
    return search_market(q)


@router.get("/{panel_type}")
async def get_panel_template(panel_type: str):
    """获取模板详情"""
    panel = get_market_panel(panel_type)
    if not panel:
        raise HTTPException(status_code=404, detail="Template not found")
    return panel


class InstallRequest(BaseModel):
    title: Optional[str] = None
    size: Optional[str] = None
    storage: Optional[dict] = None  # storage overrides


@router.post("/{panel_type}/install")
async def install_panel(panel_type: str, request: InstallRequest):
    """从市场安装 Panel"""
    from datetime import datetime
    import random
    
    # 获取模板信息
    template = get_market_panel(panel_type)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # 生成 panel ID
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = format(random.randint(0, 0xFFFF), '04x')
    panel_id = f"{panel_type}-{timestamp}-{suffix}"
    
    # 使用提供的 title 或模板默认名称
    title = request.title or template.get("name", panel_type)
    
    # 安装
    result = install_market_panel(
        panel_type=panel_type,
        panel_id=panel_id,
        title=title,
        storage_overrides=request.storage,
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="Failed to install panel")
    
    size = request.size or template.get("defaultSize", "3x2")
    
    # 添加到 layout
    add_panel_to_layout(panel_id, size=size)
    
    return {
        "success": True,
        "panelId": panel_id,
        "message": f"Installed {panel_type} panel as {panel_id}"
    }
