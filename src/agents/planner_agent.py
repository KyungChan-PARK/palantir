from .base_agent import BaseAgent, AgentConfig
from typing import Any, Dict, List


class PlannerAgent(BaseAgent):
    """중앙 오케스트레이터 역할의 에이전트"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    async def process(self, input_data: Any) -> Any:
        # 입력을 Task로 분해하는 로직 (스켈레톤)
        tasks = self.plan_tasks(input_data)
        results = []
        for task in tasks:
            # 실제로는 하위 에이전트에게 할당해야 함
            results.append({"task": task, "result": None})
        return results

    async def validate(self, output: Any) -> bool:
        # 결과 검증 로직 (스켈레톤)
        return True

    def plan_tasks(self, input_data: Any) -> List[Dict[str, Any]]:
        # 입력을 여러 Task로 분해 (스켈레톤)
        return [{"subtask": input_data}]  # 실제로는 더 세분화
