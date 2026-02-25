"""Agent API routes - AI-powered panel management."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    tool_calls: list[dict] | None = None


SYSTEM_PROMPT = """You are Hypane Assistant, an AI that helps users manage their personal dashboard.

You can:
- Create storages (JSON data containers) that panels and tasks can share
- Create panels with Jinja2 templates and Python handlers
- Create scheduled tasks that run periodically

When creating panels:
- Templates use Jinja2 syntax with access to `panel` (metadata) and `storage` (dict of storage data)
- Handlers define `on_action(action, payload, storage)` to handle user interactions
- Storage is passed as `storage['storage-id']['field']`

When creating tasks:
- Handlers define `on_schedule(storage)` for periodic execution
- Use cron expressions like '0 * * * *' (hourly) or '*/5 * * * *' (every 5 minutes)

Be concise and helpful. Create functional, well-designed panels."""


@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat with agent to manage panels."""
    from app.agent import PiMonoAgent, PANEL_TOOLS, execute_panel_tool, AgentMessage
    
    agent = PiMonoAgent()
    
    # Run agent with tools
    messages = [AgentMessage(role="user", content=request.message)]
    
    response = await agent.run_with_tools(
        user_message=request.message,
        tools=PANEL_TOOLS,
        tool_executor=execute_panel_tool,
        system_prompt=SYSTEM_PROMPT,
        max_iterations=5,
    )
    
    return ChatResponse(response=response)


@router.post("/chat/simple")
async def chat_simple(request: ChatRequest) -> ChatResponse:
    """Simple chat without tool execution (for testing)."""
    from app.agent import PANEL_TOOLS, execute_panel_tool
    
    # For now, just execute tools directly based on simple patterns
    message = request.message.lower()
    
    if "create storage" in message or "new storage" in message:
        # Extract storage name from message
        parts = request.message.split()
        storage_id = "new-storage"
        for i, p in enumerate(parts):
            if p.lower() in ["storage", "called", "named"] and i + 1 < len(parts):
                storage_id = parts[i + 1].strip("'\"")
                break
        
        result = await execute_panel_tool("create_storage", {"id": storage_id, "data": {}})
        return ChatResponse(response=result)
    
    return ChatResponse(
        response="I can help you create storages, panels, and tasks. Try:\n"
                 "- 'Create a storage called my-data'\n"
                 "- 'Create a todo panel'\n"
                 "- 'Create a task to refresh weather hourly'"
    )
