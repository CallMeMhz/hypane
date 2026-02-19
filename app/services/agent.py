import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import AsyncIterator, Optional

from app.config import PI_COMMAND, SYSTEM_SKILL, SESSIONS_DIR, DASHBOARD_EXTENSION

# 增大行缓冲区限制到 10MB
STREAM_LIMIT = 10 * 1024 * 1024


def get_system_context() -> str:
    """Generate system context with current time."""
    now = datetime.now()
    utc_now = datetime.now(timezone.utc)
    return f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')} (local), {utc_now.strftime('%Y-%m-%d %H:%M:%S')} UTC"


async def run_agent_chat(message: str) -> dict:
    """Run pi agent with a chat message and return response (non-streaming)."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        PI_COMMAND,
        "-p", message,
        "--skill", str(SYSTEM_SKILL),
        "--session-dir", str(SESSIONS_DIR),
        "--mode", "text",
    ]

    try:
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            reply = result.stdout.strip()
            dashboard_updated = "dashboard" in reply.lower() or "卡片" in reply

            return {
                "reply": reply,
                "dashboardUpdated": dashboard_updated,
            }
        else:
            return {
                "reply": f"Agent error: {result.stderr}",
                "dashboardUpdated": False,
            }
    except subprocess.TimeoutExpired:
        return {
            "reply": "Agent timeout - 请求超时",
            "dashboardUpdated": False,
        }
    except Exception as e:
        return {
            "reply": f"Error: {str(e)}",
            "dashboardUpdated": False,
        }


async def run_agent_stream(message: str, session_id: Optional[str] = None) -> AsyncIterator[str]:
    """
    Stream agent response using pi --mode json (JSONL streaming).
    
    Each web session gets its own session file for conversation continuity,
    but the agent can use dashboard_changelog tool to see history.
    """
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Use provided session_id or create a temporary one
    if session_id:
        session_file = SESSIONS_DIR / f"web-{session_id}.jsonl"
    else:
        # No session - each request is independent
        session_file = None

    # Prepend system context to message
    system_context = get_system_context()
    full_message = f"[{system_context}]\n\n{message}"

    cmd = [
        PI_COMMAND,
        "-p", full_message,
        "--skill", str(SYSTEM_SKILL),
        "-e", str(DASHBOARD_EXTENSION),
        "--mode", "json",
    ]
    
    # Only add session if provided
    if session_file:
        cmd.extend(["--session", str(session_file)])
    
    print(f"[DEBUG] Running pi (session: {session_file})", file=sys.stderr)

    # 使用更大的 limit 来处理长行
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        limit=STREAM_LIMIT,
    )

    dashboard_updated = False
    current_message_id = 0
    current_message_has_content = False
    line_count = 0

    try:
        while True:
            try:
                line = await asyncio.wait_for(process.stdout.readline(), timeout=300)
            except asyncio.TimeoutError:
                print(f"[DEBUG] Timeout after {line_count} lines", file=sys.stderr)
                break
            
            if not line:
                print(f"[DEBUG] EOF after {line_count} lines", file=sys.stderr)
                break
                
            line_count += 1
            text = line.decode("utf-8").strip()
            if not text:
                continue

            try:
                event = json.loads(text)
                event_type = event.get("type")

                # 文本增量
                if event_type == "message_update":
                    assistant_event = event.get("assistantMessageEvent", {})
                    delta_type = assistant_event.get("type")
                    
                    if delta_type == "text_start":
                        current_message_id += 1
                        current_message_has_content = False
                    
                    elif delta_type == "text_delta":
                        delta = assistant_event.get("delta", "")
                        if delta:
                            if not current_message_has_content:
                                yield f"data: {json.dumps({'type': 'message_start', 'messageId': current_message_id})}\n\n"
                                current_message_has_content = True
                            yield f"data: {json.dumps({'type': 'delta', 'content': delta, 'messageId': current_message_id})}\n\n"
                    
                    elif delta_type == "text_end":
                        if current_message_has_content:
                            yield f"data: {json.dumps({'type': 'message_end', 'messageId': current_message_id})}\n\n"
                        current_message_has_content = False

                # 工具调用开始
                elif event_type == "tool_execution_start":
                    tool_name = event.get("toolName", "")
                    tool_args = event.get("args", {})
                    
                    # 检测 dashboard 相关操作
                    if tool_name.startswith("dashboard_") and tool_name != "dashboard_list_cards" and tool_name != "dashboard_get_card":
                        dashboard_updated = True
                    
                    display_args = {}
                    if tool_name == "bash":
                        display_args = {"command": tool_args.get("command", "")[:50]}
                    elif tool_name == "read":
                        display_args = {"path": tool_args.get("path", "")}
                    elif tool_name in ("edit", "write"):
                        display_args = {"path": tool_args.get("path", "")}
                        path = tool_args.get("path", "")
                        if "dashboard" in path.lower():
                            dashboard_updated = True
                    elif tool_name.startswith("dashboard_"):
                        # 显示 dashboard 工具的参数
                        if "cardId" in tool_args:
                            display_args = {"cardId": tool_args["cardId"]}
                        elif "type" in tool_args:
                            display_args = {"type": tool_args["type"], "title": tool_args.get("title", "")}
                    
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name, 'args': display_args})}\n\n"

                # 工具调用结束
                elif event_type == "tool_execution_end":
                    tool_name = event.get("toolName", "")
                    is_error = event.get("isError", False)
                    yield f"data: {json.dumps({'type': 'tool_end', 'tool': tool_name, 'isError': is_error})}\n\n"
                
                # Retry events
                elif event_type == "auto_retry_start":
                    print(f"[DEBUG] auto_retry_start", file=sys.stderr)
                    yield f"data: {json.dumps({'type': 'status', 'message': '遇到错误，正在重试...'})}\n\n"
                
                elif event_type == "auto_retry_end":
                    success = event.get("success", False)
                    print(f"[DEBUG] auto_retry_end success={success}", file=sys.stderr)

            except json.JSONDecodeError:
                continue

    except Exception as e:
        print(f"[DEBUG] Exception: {type(e).__name__}: {e}", file=sys.stderr)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return_code = await process.wait()
    print(f"[DEBUG] Exit code: {return_code}", file=sys.stderr)
    
    yield f"data: {json.dumps({'type': 'done', 'dashboardUpdated': dashboard_updated})}\n\n"


async def run_skill(skill_path: str, task_name: str) -> dict:
    """Run a specific skill (for scheduled tasks)."""
    cmd = [
        PI_COMMAND,
        "-p", f"执行定时任务: {task_name}",
        "--skill", skill_path,
        "--session-dir", str(SESSIONS_DIR),
        "--mode", "text",
    ]

    try:
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
        }
