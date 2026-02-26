from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.models.panel import Panel
from app.services import panels_v2
from app.services.dashboard import get_panel_layout
from app.services.panel_theme import DEFAULT_COLOR, DEFAULT_ICON, get_color, get_icon_svg

router = APIRouter(tags=["panels"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/panels/{panel_id}", response_class=HTMLResponse)
async def render_panel(request: Request, panel_id: str):
    """Render a single panel as HTML (for HTMX refresh)."""
    panel = await Panel.load(panel_id)
    if panel is None:
        return HTMLResponse(
            content=f'<div class="text-red-500">Panel not found: {panel_id}</div>',
            status_code=404,
        )

    rendered_html = await panels_v2.render_panel(panel_id) or ""

    layout = await get_panel_layout(panel_id)

    icon_svg = get_icon_svg(panel.icon or DEFAULT_ICON)
    color_value = get_color(panel.headerColor or DEFAULT_COLOR)

    panel_dict = {
        **panel.to_dict(),
        "facade": rendered_html,
        "position": layout.get("position", {"x": 0, "y": 0}) if layout else {"x": 0, "y": 0},
        "size": layout.get("size", panel.size or "3x2") if layout else panel.size or "3x2",
        "iconSvg": icon_svg,
        "headerColorValue": color_value,
    }

    return templates.TemplateResponse(
        "partials/panel.html",
        {"request": request, "panel": panel_dict},
    )


@router.get("/panels/{panel_id}/content", response_class=HTMLResponse)
async def render_panel_content(panel_id: str):
    """Render only panel content (for partial HTMX refresh)."""
    rendered_html = await panels_v2.render_panel(panel_id)
    if rendered_html is None:
        return HTMLResponse(
            content='<div class="text-red-500">Panel not found</div>',
            status_code=404,
        )
    return HTMLResponse(content=rendered_html)
