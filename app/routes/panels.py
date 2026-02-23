from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.services.panels import get_panel, get_panel_facade, get_panel_data
from app.services.dashboard import get_panel_layout

router = APIRouter(tags=["panels"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/panels/{panel_id}", response_class=HTMLResponse)
async def render_panel(request: Request, panel_id: str):
    """Render a single panel as HTML."""
    panel_data = get_panel_data(panel_id)
    if panel_data is None:
        return HTMLResponse(
            content=f'<div class="text-red-500">Panel not found: {panel_id}</div>',
            status_code=404
        )
    
    facade = get_panel_facade(panel_id)
    layout = get_panel_layout(panel_id)
    
    panel = {
        **panel_data,
        "facade": facade,
        "position": layout.get("position", {"x": 0, "y": 0}) if layout else {"x": 0, "y": 0},
        "size": layout.get("size", "3x2") if layout else "3x2",
    }
    
    return templates.TemplateResponse(
        "partials/panel.html",
        {"request": request, "panel": panel}
    )
