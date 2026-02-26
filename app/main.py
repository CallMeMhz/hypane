from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import config, db
from app.config import STATIC_DIR, TEMPLATES_DIR
from app.routes import (
    api_agent,
    api_dashboards,
    api_market,
    api_panels,
    api_storage,
    api_tasks,
    chat,
    console,
    dashboard,
    history,
    panels,
    sessions,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.connect(config.MONGO_DSN, config.MONGODB_DB)

    from app.migrate import migrate_files_to_mongo
    await migrate_files_to_mongo()

    from app.services.task_scheduler import start_scheduler
    await start_scheduler()

    yield

    # Shutdown
    from app.services.task_scheduler import stop_scheduler
    stop_scheduler()
    await db.close()


app = FastAPI(title="AI Dashboard", lifespan=lifespan)

# Static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Routes
app.include_router(dashboard.router)
app.include_router(console.router)
app.include_router(panels.router)
app.include_router(api_panels.router)
app.include_router(api_dashboards.router)
app.include_router(api_market.router)
app.include_router(api_storage.router)
app.include_router(api_tasks.router)
app.include_router(api_agent.router)
app.include_router(chat.router)
app.include_router(history.router)
app.include_router(sessions.router)
