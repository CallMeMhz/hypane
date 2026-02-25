"""Simple executor - uses exec() for local development."""

import time
import json
import httpx
import builtins
import traceback
from datetime import datetime, date, timedelta

from .executor import SandboxExecutor
from .protocol import HandlerContext, HandlerResult, EventType


class SimpleExecutor(SandboxExecutor):
    """
    Simple executor using exec().
    
    WARNING: Not secure for production! Use Docker executor for untrusted code.
    """
    
    # Pre-imported modules available to handlers
    ALLOWED_MODULES = {
        'time': time,
        'json': json,
        'httpx': httpx,
        'datetime': datetime,
        'date': date,
        'timedelta': timedelta,
    }
    
    def execute(self, code: str, context: HandlerContext) -> HandlerResult:
        """Execute handler code."""
        try:
            # Remove import statements - modules are pre-provided
            lines = code.split('\n')
            filtered_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    continue
                filtered_lines.append(line)
            code = '\n'.join(filtered_lines)
            
            # Single namespace with full builtins (dev mode)
            namespace = {
                '__builtins__': builtins,
                **self.ALLOWED_MODULES,
                'storage': context.storage,
            }
            
            # Execute the handler code
            exec(code, namespace)
            
            # Call the appropriate handler function
            if context.event.type == EventType.ACTION:
                handler_fn = namespace.get('on_action')
                if handler_fn:
                    handler_fn(
                        context.event.action,
                        context.event.payload or {},
                        context.storage
                    )
                else:
                    return HandlerResult(success=False, error="on_action function not defined")
                    
            elif context.event.type == EventType.SCHEDULE:
                handler_fn = namespace.get('on_schedule')
                if handler_fn:
                    handler_fn(context.storage)
                else:
                    return HandlerResult(success=False, error="on_schedule function not defined")
            
            elif context.event.type == EventType.INIT:
                handler_fn = namespace.get('on_init')
                if handler_fn:
                    handler_fn(context.storage)
                # on_init is optional, no error if not defined
            
            return HandlerResult(success=True)
            
        except Exception as e:
            return HandlerResult(
                success=False,
                error=f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            )
