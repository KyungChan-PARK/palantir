import concurrent.futures
from typing import List

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
    """멀티 에이전트 오케스트레이터"""

    def __init__(self, execution_mode: str = "serial") -> None:
        self.planner = PlannerAgent("Planner")
        self.developer = DeveloperAgent("Developer")
        self.reviewer = ReviewerAgent("Reviewer")
        self.self_improver = SelfImprovementAgent("SelfImprover")
        # MCP 계층
        self.llm_mcp = LLMMCP()
        self.file_mcp = FileMCP()
        self.git_mcp = GitMCP()
        self.test_mcp = TestMCP()
        self.web_mcp = WebMCP()
        # 실행 모드: serial, parallel, adaptive
        self.execution_mode = execution_mode
        self.context_manager = ContextManager()

    def _execute_task(
        self, task: str, state: OrchestratorState, planner_ctx: dict
    ) -> TaskState:
        task_state = TaskState(task=task)
        retry_count = 0
        dev_ctx = self.context_manager.merge_contexts("Developer")
        reviewer_ctx = self.context_manager.merge_contexts("Reviewer")
        improver_ctx = self.context_manager.merge_contexts("SelfImprover")
        while True:
            dev_result = self.developer.process([task], state=dev_ctx)
            review = self.reviewer.process(dev_result, state=reviewer_ctx)
            task_state.test_results.append(review)
            mcp_results = self.test_mcp.run_all_checks()
            task_state.test_results.append({"mcp_checks": mcp_results})
            if not any("테스트 실패" in r.get("test_result", "") for r in review):
                break
            if retry_count >= 3:
                notify_slack(
                    f"[PalantirAIP][경고] 태스크 '{task}' 3회 연속 실패. Planner가 재계획 시도."
                )
                replanned = self.planner.process(
                    f"이 태스크를 더 세분화해서 다시 계획: {task}", state=planner_ctx
                )
                state.plan = (
                    state.plan[: state.current_task_idx]
                    + replanned
                    + state.plan[state.current_task_idx + 1 :]
                )
                retry_count = 0
                task = state.plan[state.current_task_idx]
                continue
            improvement = self.self_improver.process(review, state=improver_ctx)
            task_state.improvement_history.append(improvement)
            retry_count += 1
            task_state.fail_history.append(
                ImprovementHistory(
                    improvement=improvement, fail_loop=retry_count, review=review
                )
            )
            if retry_count == 3 and not task_state.alert_sent:
                notify_slack(
                    f"[PalantirAIP][경고] 태스크 '{task}' 3회 연속 실패. 정책 위반/중단 필요."
                )
                task_state.alert_sent = True
                state.alerts.append({"task": task, "fail_loop": retry_count})
                state.policy_triggered = True
            if state.policy_triggered:
                break
        return task_state

    def run(self, user_input: str) -> List[TaskState]:
        try:
            state = OrchestratorState(plan=[])
            planner_ctx = self.context_manager.merge_contexts("Planner")
            plan = self.planner.process(user_input, state=planner_ctx)
            state.plan = plan
            if self.execution_mode == "parallel":
                with concurrent.futures.ThreadPoolExecutor() as exe:
                    futures = [
                        exe.submit(self._execute_task, t, state, planner_ctx)
                        for t in plan
                    ]
                    for fut in concurrent.futures.as_completed(futures):
                        state.results.append(fut.result())
                        state.current_task_idx += 1
                        if state.policy_triggered:
                            break
            else:
                while state.current_task_idx < len(state.plan):
                    task = state.plan[state.current_task_idx]
                    task_state = self._execute_task(task, state, planner_ctx)
                    state.results.append(task_state)
                    state.current_task_idx += 1
                    if state.policy_triggered:
                        break
                    if (
                        self.execution_mode == "adaptive"
                        and len(state.plan) - state.current_task_idx > 1
                    ):
                        # 남은 태스크를 병렬 처리
                        remaining = state.plan[state.current_task_idx :]
                        with concurrent.futures.ThreadPoolExecutor() as exe:
                            futures = [
                                exe.submit(self._execute_task, t, state, planner_ctx)
                                for t in remaining
                            ]
                            for fut in concurrent.futures.as_completed(futures):
                                state.results.append(fut.result())
                                state.current_task_idx += 1
                                if state.policy_triggered:
                                    break
                        break
            return state.results
        except Exception as e:
            notify_slack(f"[PalantirAIP][오류] 오케스트레이터 예외 발생: {str(e)}")
            return [{"error": str(e)}]
