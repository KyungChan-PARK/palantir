from .base_agent import BaseAgent, AgentConfig
from typing import Any


class ReviewerAgent(BaseAgent):
    """코드/결과 검토 담당 에이전트"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    async def process(self, input_data: Any) -> Any:
        # 코드/결과 검토 로직 (스켈레톤)
        return {"review": "# TODO: 코드/결과 검토"}

    async def validate(self, output: Any) -> bool:
        # 검토 결과 검증 로직 (스켈레톤)
        return True
