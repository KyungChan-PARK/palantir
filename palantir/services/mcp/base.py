"""Base MCP (Model Control Plane) module."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel


class MCPConfig(BaseModel):
    """MCP configuration model."""

    api_key: str
    base_url: str
    parameters: Optional[Dict[str, Any]] = None

    class Config:
        arbitrary_types_allowed = True


class BaseMCP(ABC):
    """Base class for Model Control Plane implementations."""

    def __init__(self, config: MCPConfig):
        self.config = config

    @abstractmethod
    async def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute a command."""
        pass

    @abstractmethod
    async def register_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new agent."""
        pass

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass 