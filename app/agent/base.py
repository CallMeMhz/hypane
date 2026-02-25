"""Agent base interface - abstract class for AI agent implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Any


@dataclass
class AgentMessage:
    """Message in agent conversation."""
    role: str  # "user", "assistant", "tool"
    content: str
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None


@dataclass
class ToolDefinition:
    """Tool definition for agent."""
    name: str
    description: str
    parameters: dict  # JSON Schema


@dataclass
class ToolResult:
    """Result from tool execution."""
    tool_call_id: str
    content: str
    is_error: bool = False


class AgentBase(ABC):
    """Abstract base class for AI agents."""
    
    @abstractmethod
    async def chat(
        self,
        messages: list[AgentMessage],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> AgentMessage:
        """
        Send messages to agent and get response.
        
        Args:
            messages: Conversation history
            tools: Available tools
            system_prompt: System prompt override
            
        Returns:
            Agent response message
        """
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: list[AgentMessage],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream chat response.
        
        Yields:
            Text chunks as they arrive
        """
        pass
    
    async def run_with_tools(
        self,
        user_message: str,
        tools: list[ToolDefinition],
        tool_executor: callable,
        system_prompt: str | None = None,
        max_iterations: int = 10,
    ) -> str:
        """
        Run agent loop with tool execution.
        
        Args:
            user_message: User's input
            tools: Available tools
            tool_executor: async function(tool_name, args) -> str
            system_prompt: System prompt
            max_iterations: Max tool call iterations
            
        Returns:
            Final assistant response
        """
        messages = [AgentMessage(role="user", content=user_message)]
        
        for _ in range(max_iterations):
            response = await self.chat(messages, tools, system_prompt)
            messages.append(response)
            
            # If no tool calls, we're done
            if not response.tool_calls:
                return response.content
            
            # Execute tools
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call.get("arguments", {})
                tool_id = tool_call.get("id", tool_name)
                
                try:
                    result = await tool_executor(tool_name, tool_args)
                    messages.append(AgentMessage(
                        role="tool",
                        content=result,
                        tool_call_id=tool_id,
                    ))
                except Exception as e:
                    messages.append(AgentMessage(
                        role="tool",
                        content=f"Error: {str(e)}",
                        tool_call_id=tool_id,
                    ))
        
        return messages[-1].content if messages else ""
