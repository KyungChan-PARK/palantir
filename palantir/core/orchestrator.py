import concurrent.futures

from palantir.core.backup import notify_slack
from palantir.core.context_manager import ContextManager
from palantir.models.state import ImprovementHistory, OrchestratorState, TaskState
from palantir.services.mcp.file_mcp import FileMCP
from palantir.services.mcp.git_mcp import GitMCP
from palantir.services.mcp.llm_mcp import LLMMCP
from palantir.services.mcp.test_mcp import TestMCP
from palantir.services.mcp.web_mcp import WebMCP

from .agent_impls import (
    DeveloperAgent,
    PlannerAgent,
    ReviewerAgent,
    SelfImprovementAgent,
)


class Orchestrator:
    """에이전트와 MCP 계층을 연결하는 간소화된 오케스트레이터"""

    def __init__(self, execution_mode: str = "serial") -> None:
        self.planner = PlannerAgent("Planner")
        self.developer = DeveloperAgent("Developer")
        self.reviewer = ReviewerAgent("Reviewer")
        self.self_improver = SelfImprovementAgent("SelfImprover")
        self.llm_mcp = LLMMCP()
        self.file_mcp = FileMCP()
        self.git_mcp = GitMCP()
        self.test_mcp = TestMCP()
        self.web_mcp = WebMCP()
        self.execution_mode = execution_mode
        self.context_manager = ContextManager()

    def _process_task(self, task: str) -> TaskState:
        """Developer → Reviewer → SelfImprover 흐름을 단일 태스크에 적용"""
        task_state = TaskState(task=task)
        dev_ctx = self.context_manager.merge_contexts("Developer")
        dev_result = self.developer.process([task], state=dev_ctx)
        self.context_manager.update_agent_context(
            "Developer", "last_result", dev_result
        )

        reviewer_ctx = self.context_manager.merge_contexts("Reviewer")
        review = self.reviewer.process(dev_result, state=reviewer_ctx)
        self.context_manager.update_agent_context("Reviewer", "last_review", review)

        mcp_results = self.test_mcp.run_all_checks()
        task_state.test_results.append({"mcp_checks": mcp_results})

        fail_loop = 0
        while any("테스트 실패" in r.get("test_result", "") for r in review):
            if fail_loop >= 3:
                notify_slack(f"[PalantirAIP][경고] 태스크 '{task}' 3회 연속 실패")
                task_state.alert_sent = True
                break
            improver_ctx = self.context_manager.merge_contexts("SelfImprover")
            improvement = self.self_improver.process(review, state=improver_ctx)
            task_state.improvement_history.append(improvement)
            self.context_manager.update_agent_context(
                "SelfImprover", "last_improvement", improvement
            )
            review = self.reviewer.process(dev_result, state=reviewer_ctx)
            fail_loop += 1

        task_state.test_results.append(review)
        task_state.fail_history.append(
            ImprovementHistory(improvement=None, fail_loop=fail_loop, review=review)
        )
        return task_state

    def run(self, user_input: str):
        """사용자 입력을 받아 전체 태스크 플로우를 실행"""
        try:
            print(f"[Planner] 사용자 요구: {user_input}")
            state = OrchestratorState(plan=[])
            state.history.append(f"[Planner] 사용자 요구: {user_input}")
            planner_ctx = self.context_manager.merge_contexts("Planner")
            plan = self.planner.process(user_input, state=planner_ctx)
            print(f"[Planner] 태스크 분해 결과: {plan}")
            state.history.append(f"[Planner] 태스크 분해 결과: {plan}")
            state.plan = plan

            if self.execution_mode == "parallel":
                with concurrent.futures.ThreadPoolExecutor() as exe:
                    futures = [exe.submit(self._process_task, t) for t in plan]
                    for fut in concurrent.futures.as_completed(futures):
                        state.results.append(fut.result())
            else:
                for idx, task in enumerate(plan):
                    state.current_task_idx = idx
                    state.results.append(self._process_task(task))

            print(f"[Orchestrator] 전체 태스크 완료. 결과: {state.results}")
            state.history.append(f"[Orchestrator] 전체 태스크 완료. 결과: {state.results}")
            return state.results
        except Exception as e:  # pragma: no cover - 런타임 예외 로깅
            notify_slack(f"[PalantirAIP][오류] 오케스트레이터 예외 발생: {str(e)}")
            print(f"[오케스트레이터 오류] {str(e)}")
            if hasattr(state, "history"):
                state.history.append(f"[오케스트레이터 오류] {str(e)}")
            return {"error": str(e)}
