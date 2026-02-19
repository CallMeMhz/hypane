from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from app.services.agent import run_agent_chat, run_agent_stream

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat message, call agent, return response (non-streaming)."""
    result = await run_agent_chat(request.message)
    return JSONResponse(
        content={
            "reply": result["reply"],
            "dashboardUpdated": result.get("dashboardUpdated", False),
        },
        headers={"HX-Trigger": "dashboardUpdated"} if result.get("dashboardUpdated") else {},
    )


@router.get("/chat/stream")
async def chat_stream(message: str):
    """SSE stream for agent response."""
    return StreamingResponse(
        run_agent_stream(message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
