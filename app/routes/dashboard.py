from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.services import panels_v2
from app.services.dashboard import get_dashboard
from app.services.panel_theme import DEFAULT_COLOR, DEFAULT_ICON, get_color, get_icon_svg

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)


async def enrich_panels_for_render(panels: list) -> list:
    """Add rendered template, icon SVG, and color to each panel."""
    enriched = []
    for panel in panels:
        panel_id = panel.get("id")

        rendered_html = await panels_v2.render_panel(panel_id) or ""

        icon_name = panel.get("icon", DEFAULT_ICON)
        header_color = panel.get("headerColor", DEFAULT_COLOR)
        icon_svg = get_icon_svg(icon_name)
        color_value = get_color(header_color)

        enriched.append({
            **panel,
            "facade": rendered_html,
            "iconSvg": icon_svg,
            "headerColor": header_color,
            "headerColorValue": color_value,
        })
    return enriched


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main dashboard page."""
    dashboard = await get_dashboard()
    panels = await enrich_panels_for_render(dashboard.get("panels", []))

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "panels": panels,
            "preferences": dashboard.get("userPreferences", {}),
        },
    )


@router.get("/dashboard-panels", response_class=HTMLResponse)
async def dashboard_panels(request: Request):
    """Return just the panels HTML for HTMX refresh."""
    dashboard = await get_dashboard()
    panels = await enrich_panels_for_render(dashboard.get("panels", []))

    return templates.TemplateResponse(
        "partials/panels_grid.html",
        {
            "request": request,
            "panels": panels,
        },
    )
