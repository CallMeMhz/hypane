"""Sandbox executor interface."""

from abc import ABC, abstractmethod
from .protocol import HandlerContext, HandlerResult


class SandboxExecutor(ABC):
    """Abstract base class for sandbox executors."""
    
    @abstractmethod
    def execute(self, code: str, context: HandlerContext) -> HandlerResult:
        """
        Execute handler code in sandbox.
        
        Args:
            code: Python code string (handler.py content)
            context: Handler context with storage and event
            
        Returns:
            HandlerResult with success status and optional error
        """
        pass


def get_executor(executor_type: str = "simple") -> SandboxExecutor:
    """Factory function to get executor instance."""
    if executor_type == "simple":
        from .simple import SimpleExecutor
        return SimpleExecutor()
    elif executor_type == "docker":
        from .docker import DockerExecutor
        return DockerExecutor()
    else:
        raise ValueError(f"Unknown executor type: {executor_type}")
