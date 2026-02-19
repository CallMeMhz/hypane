from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.services.dashboard import get_dashboard

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main dashboard page."""
    dashboard = get_dashboard()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "cards": dashboard.get("cards", []),
            "preferences": dashboard.get("userPreferences", {}),
        },
    )


@router.get("/dashboard-cards", response_class=HTMLResponse)
async def dashboard_cards(request: Request):
    """Return just the cards HTML for HTMX refresh."""
    dashboard = get_dashboard()
    return templates.TemplateResponse(
        "partials/cards_grid.html",
        {
            "request": request,
            "cards": dashboard.get("cards", []),
        },
    )
