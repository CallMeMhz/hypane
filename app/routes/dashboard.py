from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.services import panels_v2
from app.services.dashboard import get_dashboard, list_dashboards
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
async def index():
    """Redirect to default dashboard."""
    return RedirectResponse("/d/default", status_code=302)


@router.get("/d/{dashboard_id}", response_class=HTMLResponse)
async def dashboard_page(request: Request, dashboard_id: str):
    """Render a specific dashboard page."""
    dashboard = await get_dashboard(dashboard_id=dashboard_id)
    dashboards = await list_dashboards()

    # Ensure current dashboard appears in list (auto-created by get_dashboard)
    if not any(d["id"] == dashboard_id for d in dashboards):
        dashboards.append({
            "id": dashboard_id,
            "name": dashboard_id.replace("-", " ").title(),
            "panel_count": len(dashboard.get("panels", [])),
        })

    panels = await enrich_panels_for_render(dashboard.get("panels", []))

    all_panels = await panels_v2.list_panels()
    dashboard_panel_ids = [p["id"] for p in dashboard.get("panels", [])]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "panels": panels,
            "preferences": dashboard.get("userPreferences", {}),
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard.get("name", dashboard_id),
            "dashboards": dashboards,
            "all_panels": all_panels,
            "dashboard_panel_ids": dashboard_panel_ids,
        },
    )


@router.get("/d/{dashboard_id}/content", response_class=HTMLResponse)
async def dashboard_content(request: Request, dashboard_id: str):
    """Return just the main content area for HTMX dashboard switch."""
    dashboard = await get_dashboard(dashboard_id=dashboard_id)
    panels = await enrich_panels_for_render(dashboard.get("panels", []))

    return templates.TemplateResponse(
        "partials/dashboard_content.html",
        {
            "request": request,
            "panels": panels,
            "dashboard_id": dashboard_id,
        },
    )


@router.get("/d/{dashboard_id}/panels", response_class=HTMLResponse)
async def dashboard_panels(request: Request, dashboard_id: str):
    """Return just the panels HTML for HTMX refresh."""
    dashboard = await get_dashboard(dashboard_id=dashboard_id)
    panels = await enrich_panels_for_render(dashboard.get("panels", []))

    return templates.TemplateResponse(
        "partials/panels_grid.html",
        {
            "request": request,
            "panels": panels,
        },
    )


# Keep old route for backwards compatibility during transition
@router.get("/dashboard-panels", response_class=HTMLResponse)
async def dashboard_panels_legacy(request: Request):
    """Legacy HTMX refresh endpoint."""
    return await dashboard_panels(request, "default")
