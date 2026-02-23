"""Chat session API routes."""

import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException

from app.config import SESSIONS_DIR

router = APIRouter(tags=["sessions"])


def extract_text_content(content):
    """Extract text from message content (can be string or array)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                return item.get('text', '')
    return ''


def parse_session_file(filepath: Path) -> dict:
    """Parse a session file and extract metadata."""
    messages = []
    first_user_message = None
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    # pi session format: type=message contains the actual message
                    if entry.get('type') == 'message':
                        msg = entry.get('message', {})
                        role = msg.get('role')
                        content = extract_text_content(msg.get('content', ''))
                        
                        if role == 'user' and content and not first_user_message:
                            # Skip system context prefix, get actual user message
                            if '\n\n' in content:
                                # User message is after the context block
                                parts = content.split('\n\n')
                                # Find first part that doesn't look like context
                                for part in reversed(parts):
                                    if not part.startswith('[Current time:') and not part.startswith('[') and part.strip():
                                        first_user_message = part[:100]
                                        break
                            if not first_user_message:
                                first_user_message = content[:100]
                        
                        messages.append({'role': role, 'content': content})
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    
    # Get file modification time
    mtime = filepath.stat().st_mtime
    last_timestamp = datetime.fromtimestamp(mtime).isoformat()
    
    return {
        'id': filepath.stem,
        'filename': filepath.name,
        'preview': first_user_message or '(empty)',
        'messageCount': len(messages),
        'updatedAt': last_timestamp,
    }


@router.get("/api/sessions")
async def list_sessions():
    """List all chat sessions."""
    if not SESSIONS_DIR.exists():
        return []
    
    sessions = []
    for f in SESSIONS_DIR.glob("web-*.jsonl"):
        sessions.append(parse_session_file(f))
    
    # Sort by updated time, newest first
    sessions.sort(key=lambda s: s['updatedAt'], reverse=True)
    return sessions


@router.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get messages from a specific session."""
    filepath = SESSIONS_DIR / f"{session_id}.jsonl"
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = []
    pending_tools = {}  # tool_call_id -> message index
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    
                    # pi session format: type=message
                    if entry.get('type') == 'message':
                        msg = entry.get('message', {})
                        role = msg.get('role', 'unknown')
                        
                        # Skip toolResult messages (just mark tool status)
                        if role == 'toolResult':
                            tool_id = msg.get('toolCallId', '')
                            is_error = msg.get('isError', False)
                            if tool_id in pending_tools and is_error:
                                idx = pending_tools[tool_id]
                                if idx < len(messages):
                                    messages[idx]['status'] = 'error'
                            continue
                        
                        content_items = msg.get('content', [])
                        
                        # Handle string content
                        if isinstance(content_items, str):
                            content_items = [{'type': 'text', 'text': content_items}]
                        
                        for item in content_items:
                            if isinstance(item, dict):
                                item_type = item.get('type')
                                
                                # Text content
                                if item_type == 'text':
                                    text = item.get('text', '')
                                    if not text:
                                        continue
                                    
                                    # For user messages, strip the system context
                                    if role == 'user' and '\n\n' in text:
                                        parts = text.split('\n\n')
                                        for part in reversed(parts):
                                            if not part.startswith('[Current time:') and not part.startswith('[') and part.strip():
                                                text = part
                                                break
                                    
                                    messages.append({
                                        'role': role,
                                        'content': text
                                    })
                                
                                # Tool call (from assistant)
                                elif item_type == 'toolCall':
                                    tool_id = item.get('id', '')
                                    tool_name = item.get('name', 'tool')
                                    tool_args = item.get('arguments', {})
                                    
                                    display = tool_name
                                    if tool_args.get('command'):
                                        display += f": {tool_args['command'][:50]}"
                                    elif tool_args.get('path'):
                                        display += f": {tool_args['path']}"
                                    elif tool_args.get('panelId'):
                                        display += f": {tool_args['panelId']}"
                                    
                                    messages.append({
                                        'role': 'tool',
                                        'content': display,
                                        'status': 'done'
                                    })
                                    pending_tools[tool_id] = len(messages) - 1
                            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {'id': session_id, 'messages': messages}


@router.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    filepath = SESSIONS_DIR / f"{session_id}.jsonl"
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    
    filepath.unlink()
    return {'success': True}
