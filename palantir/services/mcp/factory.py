"""MCP factory module."""

from typing import Dict, Type

from palantir.core.exceptions import MCPError
from palantir.services.mcp.base import BaseMCP, MCPConfig
from palantir.services.mcp.openai import OpenAIMCP


class MCPFactory:
    """Factory class for creating MCP instances."""

    _registry: Dict[str, Type[BaseMCP]] = {
        "openai": OpenAIMCP
    }

    @classmethod
    def register(cls, name: str, mcp_class: Type[BaseMCP]) -> None:
        """Register a new MCP implementation."""
        cls._registry[name] = mcp_class

    @classmethod
    def create(cls, name: str, config: MCPConfig) -> BaseMCP:
        """Create an MCP instance."""
        if name not in cls._registry:
            raise MCPError(f"Unknown MCP type: {name}")
        return cls._registry[name](config)

    @classmethod
    def get_registered_mcps(cls) -> Dict[str, Type[BaseMCP]]:
        """Get all registered MCP implementations."""
        return cls._registry.copy() 