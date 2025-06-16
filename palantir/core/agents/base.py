from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

from ..exceptions import AgentError, MCPError
from ...services.mcp.llm_mcp import LLMMCP


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, config: Dict[str, Any], mcp_config: Optional[Dict[str, Any]] = None) -> None:
        self.validate_config(config)
        self.name = config["name"]
        self.type = config.get("type")
        self.model = config.get("model")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 512)
        self.memory: Dict[str, Any] = {}
        self.error_handlers: Dict[type, Callable[[Exception], None]] = {}
        self.llm = LLMMCP()

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> None:
        required = ["name", "type", "model", "temperature", "max_tokens"]
        for field in required:
            if field not in config:
                raise ValueError("필수 설정 누락")
        if not isinstance(config.get("temperature"), (int, float)):
            raise ValueError("잘못된 설정 타입")

    async def think(self, prompt: str) -> Any:
        try:
            return await self.llm.generate(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except MCPError as e:
            raise AgentError("LLM 처리 중 오류 발생") from e

    async def execute_tool(self, tool_name: str, tool_func: Callable[..., Any], args: Optional[Dict[str, Any]] = None) -> Any:
        try:
            return tool_func(**(args or {}))
        except Exception as exc:
            raise AgentError("도구 실행 중 오류 발생") from exc

    def get_memory(self, key: str, default: Optional[Any] = None) -> Any:
        return self.memory.get(key, default)

    def update_memory(self, key: str, value: Any) -> None:
        self.memory[key] = value

    def clear_memory(self) -> None:
        self.memory.clear()

    async def handle_error(self, error: Exception, task: str) -> None:
        handler = self.error_handlers.get(type(error))
        if handler:
            handler(error)
        else:
            raise AgentError(f"{task} 중 오류 발생") from error

    @abstractmethod
    def process(self, input_data: Any, state: Optional[Dict[str, Any]] = None) -> Any:
        raise NotImplementedError
