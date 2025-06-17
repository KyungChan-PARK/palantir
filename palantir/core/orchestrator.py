import concurrent.futures
from typing import List, Any, Tuple

from palantir.core.backup import notify_slack
from palantir.core.context_manager import ContextManager
from palantir.models.state import OrchestratorState, TaskState, ImprovementHistory
from palantir.services.mcp.file_mcp import FileMCP
from palantir.services.mcp.git_mcp import GitMCP
from palantir.services.mcp.llm_mcp import LLMMCP
from palantir.services.mcp.test_mcp import TestMCP
from palantir.services.mcp.web_mcp import WebMCP

from .agent_impls import PlannerAgent, DeveloperAgent, ReviewerAgent, SelfImprovementAgent


class Orchestrator:
    """Connects agents and MCP layers into a single loop."""

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

        # serial | parallel | adaptive
        self.execution_mode = execution_mode
        self.context_manager = ContextManager()

    def _process_task(self, task: str, state: OrchestratorState, planner_ctx: dict) -> Tuple[bool, TaskState]:
        """Process a single task with retry and self improvement."""
        task_state = TaskState(task=task)

        # Developer phase
        dev_ctx = self.context_manager.merge_contexts("Developer")
        dev_result = self.developer.process([task], state=dev_ctx)
        self.context_manager.update_agent_context("Developer", "last_result", dev_result)

        # Reviewer phase
        reviewer_ctx = self.context_manager.merge_contexts("Reviewer")
        review = self.reviewer.process(dev_result, state=reviewer_ctx)
        self.context_manager.update_agent_context("Reviewer", "last_review", review)

        # MCP checks
        mcp_results = self.test_mcp.run_all_checks()
        task_state.test_results.append({"mcp_checks": mcp_results})
        fail_loop = 0

        while any("테스트 실패" in r.get("test_result", "") for r in review):
            if fail_loop >= 3:
                notify_slack(
                    f"[PalantirAIP][경고] 태스크 '{task}' 3회 연속 실패. Planner가 재계획 시도.")
                replanned = self.planner.process(
                    f"이 태스크를 더 세분화해서 다시 계획: {task}", state=planner_ctx
                )
                return False, replanned

            improver_ctx = self.context_manager.merge_contexts("SelfImprover")
            improvement = self.self_improver.process(review, state=improver_ctx)
            task_state.improvement_history.append(improvement)
            self.context_manager.update_agent_context("SelfImprover", "last_improvement", improvement)

            review = self.reviewer.process(dev_result, state=reviewer_ctx)
            fail_loop += 1
            task_state.fail_history.append(
                ImprovementHistory(improvement=improvement, fail_loop=fail_loop, review=review)
            )
            if fail_loop == 3 and not task_state.alert_sent:
                notify_slack(
                    f"[PalantirAIP][경고] 태스크 '{task}' 3회 연속 실패. 정책 위반/중단 필요.")
                task_state.alert_sent = True
                state.alerts.append({"task": task, "fail_loop": fail_loop})
                state.policy_triggered = True

        task_state.test_results.append(review)
        return True, task_state

    def run(self, user_input: str) -> List[Any]:
        state = OrchestratorState(plan=[])
        try:
            state.history.append(f"[Planner] 사용자 요구: {user_input}")
            planner_ctx = self.context_manager.merge_contexts("Planner")
            plan = self.planner.process(user_input, state=planner_ctx)
            state.plan = plan
            state.history.append(f"[Planner] 태스크 분해 결과: {plan}")

            while state.current_task_idx < len(state.plan):
                task = state.plan[state.current_task_idx]
                state.history.append(
                    f"[Orchestrator] 현재 태스크({state.current_task_idx + 1}/{len(state.plan)}): {task}"
                )

                if self.execution_mode == "parallel":
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = [
                            executor.submit(self._process_task, t, state, planner_ctx)
                            for t in state.plan[state.current_task_idx :]
                        ]
                        results = [f.result() for f in futures]
                    # Flatten results
                    state.results.extend(r for success, r in results if success)
                    # Skip remaining tasks since processed in parallel
                    break
                elif self.execution_mode == "adaptive" and len(state.plan) > 3:
                    self.execution_mode = "parallel"
                    continue
                else:
                    success, result = self._process_task(task, state, planner_ctx)
                    if success:
                        state.results.append(result)
                        state.current_task_idx += 1
                    else:  # replanned tasks returned
                        state.plan = (
                            state.plan[: state.current_task_idx] + result + state.plan[state.current_task_idx + 1 :]
                        )

            state.history.append(f"[Orchestrator] 전체 태스크 완료. 결과: {state.results}")
            return state.results
        except Exception as exc:
            notify_slack(f"[PalantirAIP][오류] 오케스트레이터 예외 발생: {exc}")
            state.history.append(f"[오케스트레이터 오류] {exc}")
            return {"error": str(exc)}

