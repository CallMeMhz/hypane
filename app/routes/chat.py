from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.services.agent import run_agent_chat, run_agent_stream

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


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


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    SSE stream for agent response.
    
    If session_id is provided, conversation continues from previous messages.
    Otherwise, each request is independent (agent uses tools to see history).
    """
    return StreamingResponse(
        run_agent_stream(request.message, request.session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
