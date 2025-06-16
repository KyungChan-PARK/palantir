from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """에이전트 설정을 위한 기본 모델"""

    name: str = Field(..., description="에이전트 이름")
    description: str = Field(..., description="에이전트 설명")
    model: str = Field(..., description="사용할 LLM 모델")
    temperature: float = Field(default=0.7, description="생성 온도")
    max_tokens: int = Field(default=2000, description="최대 토큰 수")
    system_prompt: str = Field(..., description="시스템 프롬프트")


class BaseAgent(ABC):
    """모든 에이전트의 기본 클래스"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._initialize()

    def _initialize(self) -> None:
        """에이전트 초기화"""
        pass

    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """입력 데이터를 처리하는 메서드"""
        pass

    @abstractmethod
    async def validate(self, output: Any) -> bool:
        """출력 결과를 검증하는 메서드"""
        pass

    async def execute(self, input_data: Any) -> Any:
        """에이전트 실행 파이프라인"""
        result = await self.process(input_data)
        if await self.validate(result):
            return result
        raise ValueError("에이전트 실행 결과가 유효하지 않습니다.")

    def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 정보 반환"""
        return {
            "name": self.config.name,
            "description": self.config.description,
            "model": self.config.model,
            "temperature": self.config.temperature,
        }
