"""Pi-mono agent implementation - wraps pi CLI for agent capabilities."""

import asyncio
import json
import os
import subprocess
import tempfile
from typing import AsyncIterator

from .base import AgentBase, AgentMessage, ToolDefinition


class PiMonoAgent(AgentBase):
    """
    Agent implementation using pi-mono CLI.
    
    Delegates to pi CLI with custom tools, disabling coding agent capabilities.
    """
    
    def __init__(
        self,
        model: str = "sonnet",
        pi_path: str = "pi",
    ):
        self.model = model
        self.pi_path = pi_path
    
    async def chat(
        self,
        messages: list[AgentMessage],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> AgentMessage:
        """Send messages to pi and get response."""
        # For simple chat without tools, use direct API call
        # For now, implement basic version
        
        # Build conversation for pi
        prompt = self._build_prompt(messages, system_prompt)
        
        # Run pi in non-interactive mode
        result = await self._run_pi(prompt, tools)
        
        return AgentMessage(role="assistant", content=result)
    
    async def chat_stream(
        self,
        messages: list[AgentMessage],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream chat response from pi."""
        prompt = self._build_prompt(messages, system_prompt)
        
        async for chunk in self._run_pi_stream(prompt, tools):
            yield chunk
    
    def _build_prompt(
        self,
        messages: list[AgentMessage],
        system_prompt: str | None = None,
    ) -> str:
        """Build prompt string from messages."""
        parts = []
        
        if system_prompt:
            parts.append(f"[System]: {system_prompt}\n")
        
        for msg in messages:
            if msg.role == "user":
                parts.append(msg.content)
            elif msg.role == "assistant":
                parts.append(f"[Assistant]: {msg.content}")
            elif msg.role == "tool":
                parts.append(f"[Tool Result]: {msg.content}")
        
        return "\n".join(parts)
    
    async def _run_pi(
        self,
        prompt: str,
        tools: list[ToolDefinition] | None = None,
    ) -> str:
        """Run pi CLI and return response."""
        # Create temp file for prompt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            prompt_file = f.name
        
        try:
            cmd = [
                self.pi_path,
                "--model", self.model,
                "--non-interactive",
                "--prompt-file", prompt_file,
            ]
            
            # Add tools if provided
            if tools:
                tools_json = json.dumps([{
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                } for t in tools])
                cmd.extend(["--tools", tools_json])
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                return f"Error: {stderr.decode()}"
            
            return stdout.decode()
            
        finally:
            os.unlink(prompt_file)
    
    async def _run_pi_stream(
        self,
        prompt: str,
        tools: list[ToolDefinition] | None = None,
    ) -> AsyncIterator[str]:
        """Run pi CLI and stream response."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            prompt_file = f.name
        
        try:
            cmd = [
                self.pi_path,
                "--model", self.model,
                "--non-interactive",
                "--prompt-file", prompt_file,
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            while True:
                chunk = await proc.stdout.read(100)
                if not chunk:
                    break
                yield chunk.decode()
            
            await proc.wait()
            
        finally:
            os.unlink(prompt_file)
