"""OpenAI MCP implementation."""

import json
from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from palantir.core.exceptions import MCPError
from palantir.services.mcp.base import BaseMCP, MCPConfig


class OpenAIMCP(BaseMCP):
    """OpenAI MCP implementation."""

    def __init__(self, config: MCPConfig):
        super().__init__(config)
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            **config.parameters or {}
        )

    async def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute a command using OpenAI API."""
        try:
            response = await self.client.chat.completions.create(
                messages=[{"role": "user", "content": command}],
                **kwargs
            )
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "usage": response.usage.model_dump() if response.usage else None
            }
        except Exception as e:
            raise MCPError(f"OpenAI API error: {str(e)}")

    async def register_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new agent with OpenAI."""
        try:
            # OpenAI doesn't have a direct agent registration API
            # This is a placeholder for future implementation
            return {
                "success": True,
                "agent_id": "openai_default",
                "config": config
            }
        except Exception as e:
            raise MCPError(f"Failed to register agent: {str(e)}")

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.client.close() 