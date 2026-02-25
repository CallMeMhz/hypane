"""Docker executor - placeholder for production sandbox."""

from .executor import SandboxExecutor
from .protocol import HandlerContext, HandlerResult


class DockerExecutor(SandboxExecutor):
    """
    Docker-based executor for secure code execution.
    
    TODO: Implement using Docker containers with Python slim image.
    """
    
    def __init__(self, image: str = "python:3.12-slim", timeout: int = 30):
        self.image = image
        self.timeout = timeout
    
    def execute(self, code: str, context: HandlerContext) -> HandlerResult:
        """Execute handler code in Docker container."""
        # TODO: Implement Docker execution
        # 1. Create container from pool or spin up new one
        # 2. Copy code and context into container
        # 3. Execute handler
        # 4. Read back modified storage
        # 5. Cleanup
        
        return HandlerResult(
            success=False,
            error="Docker executor not implemented yet. Use simple executor for development."
        )
