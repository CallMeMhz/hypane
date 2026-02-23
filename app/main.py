from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import STATIC_DIR, TEMPLATES_DIR
from app.routes import dashboard, chat, history, tasks, sessions, panels, api_panels

app = FastAPI(title="AI Dashboard")

# Static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Routes
app.include_router(dashboard.router)
app.include_router(panels.router)
app.include_router(api_panels.router)
app.include_router(chat.router)
app.include_router(history.router)
app.include_router(tasks.router)
app.include_router(sessions.router)
