from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.services.dashboard import get_card

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/cards/{card_id}", response_class=HTMLResponse)
async def get_card_html(request: Request, card_id: str):
    """Return a single card HTML fragment for HTMX."""
    card = get_card(card_id)
    if not card:
        return HTMLResponse(content="", status_code=404)
    
    return templates.TemplateResponse(
        "partials/card.html",
        {
            "request": request,
            "card": card,
        },
    )
