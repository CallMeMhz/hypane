from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.services.dashboard import get_dashboard
from app.services.panels import get_panel_facade, get_panel_data
from app.services.panel_theme import get_icon_svg, get_color, DEFAULT_COLOR, DEFAULT_ICON

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)


def enrich_panels_with_facade(panels: list) -> list:
    """Add facade HTML, icon, and color to each panel."""
    enriched = []
    for panel in panels:
        panel_id = panel.get("id")
        
        # Get facade
        facade = get_panel_facade(panel_id)
        
        # Get panel data for headerColor and icon
        data = get_panel_data(panel_id) or {}
        header_color = data.get("headerColor", DEFAULT_COLOR)
        icon_name = data.get("icon", DEFAULT_ICON)
        
        # Get icon and color
        icon_svg = get_icon_svg(icon_name)
        color_value = get_color(header_color)
        
        enriched.append({
            **panel,
            "facade": facade,
            "iconSvg": icon_svg,
            "headerColor": header_color,
            "headerColorValue": color_value,
        })
    return enriched


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main dashboard page."""
    dashboard = get_dashboard()
    
    # v2 format: panels
    panels = dashboard.get("panels", [])
    if panels:
        panels = enrich_panels_with_facade(panels)
    
    # v1 fallback: cards
    cards = dashboard.get("cards", [])
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "panels": panels,
            "cards": cards,
            "preferences": dashboard.get("userPreferences", {}),
        },
    )


@router.get("/dashboard-cards", response_class=HTMLResponse)
async def dashboard_cards(request: Request):
    """Return just the panels HTML for HTMX refresh."""
    dashboard = get_dashboard()
    
    # v2 format: panels
    panels = dashboard.get("panels", [])
    if panels:
        panels = enrich_panels_with_facade(panels)
    
    # v1 fallback: cards
    cards = dashboard.get("cards", [])
    
    return templates.TemplateResponse(
        "partials/panels_grid.html",
        {
            "request": request,
            "panels": panels,
            "cards": cards,
        },
    )
