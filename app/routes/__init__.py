from app.routes.dashboard import router as dashboard_router
from app.routes.panels import router as panels_router
from app.routes.api_panels import router as api_panels_router
from app.routes.chat import router as chat_router

__all__ = ["dashboard_router", "panels_router", "api_panels_router", "chat_router"]
