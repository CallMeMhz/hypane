from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import STATIC_DIR, TEMPLATES_DIR
from app.routes import dashboard, console, chat, history, sessions, panels, api_panels, api_market, api_storage, api_tasks, api_agent

app = FastAPI(title="AI Dashboard")

# Static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Routes
app.include_router(dashboard.router)
app.include_router(console.router)
app.include_router(panels.router)
app.include_router(api_panels.router)
app.include_router(api_market.router)
app.include_router(api_storage.router)
app.include_router(api_tasks.router)
app.include_router(api_agent.router)
app.include_router(chat.router)
app.include_router(history.router)
app.include_router(sessions.router)


# Lifecycle events
@app.on_event("startup")
async def startup_event():
    """Start task scheduler on app startup."""
    from app.services.task_scheduler import start_scheduler
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """Stop task scheduler on app shutdown."""
    from app.services.task_scheduler import stop_scheduler
    stop_scheduler()
