from .base_agent import BaseAgent, AgentConfig
from typing import Any


class DeveloperAgent(BaseAgent):
    """코드 생성/수정 담당 에이전트"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    async def process(self, input_data: Any) -> Any:
        # 코드 생성/수정 로직 (스켈레톤)
        return {"code": "# TODO: 코드 생성"}

    async def validate(self, output: Any) -> bool:
        # 코드 검증 로직 (스켈레톤)
        return True
