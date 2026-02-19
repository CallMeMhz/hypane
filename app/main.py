from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import STATIC_DIR, TEMPLATES_DIR
from app.routes import dashboard, cards, chat, api_cards

app = FastAPI(title="AI Dashboard")

# Static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Routes
app.include_router(dashboard.router)
app.include_router(cards.router)
app.include_router(chat.router)
app.include_router(api_cards.router)
