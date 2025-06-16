from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class MCPContext(BaseModel):
    """MCP 컨텍스트 모델"""

    request_id: UUID
    agent_id: str
    task_type: str
    parameters: Dict[str, Any]
    metadata: Dict[str, Any] = {}


class MCPResponse(BaseModel):
    """MCP 응답 모델"""

    request_id: UUID
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class MCPTool(BaseModel):
    """MCP 도구 모델"""

    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str]
    handler: str


class MCPBase(ABC):
    """MCP 기본 인터페이스"""

    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}

    @abstractmethod
    async def process_request(self, context: MCPContext) -> MCPResponse:
        """요청 처리"""
        pass

    @abstractmethod
    async def handle_error(self, error: Exception, context: MCPContext) -> MCPResponse:
        """에러 처리"""
        pass

    @abstractmethod
    async def register_tool(self, tool: MCPTool) -> bool:
        """도구 등록"""
        pass

    @abstractmethod
    async def validate_context(self, context: MCPContext) -> bool:
        """컨텍스트 유효성 검증"""
        pass


class LLMMCPHandler(MCPBase):
    """LLM MCP 핸들러"""

    async def process_request(self, context: MCPContext) -> MCPResponse:
        try:
            # 컨텍스트 유효성 검증
            if not await self.validate_context(context):
                raise ValueError("Invalid context")

            # LLM 요청 처리
            result = await self._call_llm(context)

            return MCPResponse(
                request_id=context.request_id, status="success", result=result
            )

        except Exception as e:
            return await self.handle_error(e, context)

    async def handle_error(self, error: Exception, context: MCPContext) -> MCPResponse:
        return MCPResponse(
            request_id=context.request_id, status="error", error=str(error)
        )

    async def register_tool(self, tool: MCPTool) -> bool:
        self.tools[tool.name] = tool
        return True

    async def validate_context(self, context: MCPContext) -> bool:
        return (
            context.task_type in ["completion", "chat", "embedding"]
            and "model" in context.parameters
            and "prompt" in context.parameters
        )

    async def _call_llm(self, context: MCPContext) -> Dict[str, Any]:
        """실제 LLM 호출 구현"""
        # TODO: 실제 LLM 서비스 연동
        return {
            "text": "Sample response",
            "tokens": 10,
            "model": context.parameters["model"],
        }


class FileMCPHandler(MCPBase):
    """파일 시스템 MCP 핸들러"""

    async def process_request(self, context: MCPContext) -> MCPResponse:
        try:
            if not await self.validate_context(context):
                raise ValueError("Invalid context")

            result = await self._handle_file_operation(context)

            return MCPResponse(
                request_id=context.request_id, status="success", result=result
            )

        except Exception as e:
            return await self.handle_error(e, context)

    async def handle_error(self, error: Exception, context: MCPContext) -> MCPResponse:
        return MCPResponse(
            request_id=context.request_id, status="error", error=str(error)
        )

    async def register_tool(self, tool: MCPTool) -> bool:
        self.tools[tool.name] = tool
        return True

    async def validate_context(self, context: MCPContext) -> bool:
        return (
            context.task_type in ["read", "write", "delete", "list"]
            and "path" in context.parameters
        )

    async def _handle_file_operation(self, context: MCPContext) -> Dict[str, Any]:
        """실제 파일 시스템 작업 구현"""
        # TODO: 실제 파일 시스템 작업 구현
        return {"success": True, "path": context.parameters["path"]}
