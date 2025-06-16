from typing import Any, Dict, List
from src.agents.planner_agent import PlannerAgent
from src.agents.developer_agent import DeveloperAgent
from src.agents.reviewer_agent import ReviewerAgent
from src.agents.base_agent import AgentConfig
from src.agents.self_improvement_agent import SelfImprovementAgent


class Orchestrator:
    """멀티에이전트 오케스트레이션 담당"""

    def __init__(
        self,
        planner_cfg: AgentConfig,
        dev_cfg: AgentConfig,
        rev_cfg: AgentConfig,
        selfimp_cfg: AgentConfig = None,
    ):
        self.planner = PlannerAgent(planner_cfg)
        self.developer = DeveloperAgent(dev_cfg)
        self.reviewer = ReviewerAgent(rev_cfg)
        if selfimp_cfg:
            self.self_improver = SelfImprovementAgent(selfimp_cfg)
        else:
            self.self_improver = None

    async def run(self, user_input: Any) -> Dict[str, Any]:
        # 1. Planner가 Task 분해
        plan = await self.planner.process(user_input)
        results = []
        # 2. Developer가 각 Task 처리
        for task in plan:
            dev_result = await self.developer.process(task)
            # 3. Reviewer가 결과 검토
            review = await self.reviewer.process(dev_result)
            results.append({"task": task, "dev_result": dev_result, "review": review})
        return {"results": results}

    async def run_self_improvement(self, input_data: Any = None) -> dict:
        """자가 개선 루프 실행"""
        if not self.self_improver:
            raise RuntimeError("SelfImprovementAgent가 설정되지 않았습니다.")
        result = await self.self_improver.process(input_data)
        return result
