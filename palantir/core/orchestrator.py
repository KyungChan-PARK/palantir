import concurrent.futures

from palantir.core.backup import notify_slack
from palantir.core.context_manager import ContextManager
from palantir.models.state import (ImprovementHistory, OrchestratorState,
                                   TaskState)
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
    """에이전트와 MCP 계층을 연결하는 오케스트레이터 (그래프형 분기/병렬/에러복구/최신 패턴 지원)"""
    def __init__(self, execution_mode: str = "serial"):
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
        # 실행 모드: serial(직렬), parallel(병렬), adaptive(적응형)
        self.execution_mode = execution_mode
        # 계층형 컨텍스트/메모리
        self.context_manager = ContextManager()

    def run(self, user_input: str):
        try:
            print(f"[Planner] 사용자 요구: {user_input}")
            state = OrchestratorState(plan=[])
            state.history.append(f"[Planner] 사용자 요구: {user_input}")
            # --- Planner 컨텍스트 병합 및 주입 ---
            planner_ctx = self.context_manager.merge_contexts("Planner")
            plan = self.planner.process(user_input, state=planner_ctx)
            print(f"[Planner] 태스크 분해 결과: {plan}")
            state.history.append(f"[Planner] 태스크 분해 결과: {plan}")
            state.plan = plan
            while state.current_task_idx < len(state.plan):
                task = state.plan[state.current_task_idx]
                print(f"[Orchestrator] 현재 태스크({state.current_task_idx+1}/{len(state.plan)}): {task}")
                state.history.append(f"[Orchestrator] 현재 태스크({state.current_task_idx+1}/{len(state.plan)}): {task}")
                task_state = TaskState(task=task)
                # --- 실행 모드 분기 ---
                if self.execution_mode == "parallel":
                    # TODO: 병렬 실행(예: 여러 태스크 독립적일 때)
                    # concurrent.futures 등 활용, 결과 취합
                    pass  # 후속 구현
                elif self.execution_mode == "adaptive":
                    # TODO: 적응형 실행(태스크/에이전트 동적 분기/병렬/토론)
                    # 예: 태스크 난이도/의존성/실패율에 따라 실행 방식 결정
                    pass  # 후속 구현
                else:
                    # --- Developer 컨텍스트 병합 및 주입 ---
                    dev_ctx = self.context_manager.merge_contexts("Developer")
                    dev_result = self.developer.process([task], state=dev_ctx)
            print(f"[Developer] 코드 생성/저장 결과: {dev_result}")
                state.history.append(f"[Developer] 코드 생성/저장 결과: {dev_result}")
                    # --- Developer 실행 후 컨텍스트 갱신 예시(스텁) ---
                    self.context_manager.update_agent_context("Developer", "last_result", dev_result)
                    # --- Reviewer 컨텍스트 병합 및 주입 ---
                    reviewer_ctx = self.context_manager.merge_contexts("Reviewer")
                    review = self.reviewer.process(dev_result, state=reviewer_ctx)
                print(f"[Reviewer] 테스트/리뷰 결과: {review}")
                state.history.append(f"[Reviewer] 테스트/리뷰 결과: {review}")
                    self.context_manager.update_agent_context("Reviewer", "last_review", review)
                # MCP 계층 품질/보안/정적분석 자동화 실행 및 기록
                mcp_results = self.test_mcp.run_all_checks()
                task_state.test_results.append({"mcp_checks": mcp_results})
                state.history.append(f"[MCP] 품질/보안/정적분석 결과: {mcp_results}")
                fail_loop = 0
                while any('테스트 실패' in r.get('test_result','') for r in review):
                    if fail_loop >= 3:
                        print(f"[Orchestrator] 3회 연속 실패, Planner가 태스크 재분해/재계획 시도")
                        state.history.append(f"[Orchestrator] 3회 연속 실패, Planner가 태스크 재분해/재계획 시도")
                        notify_slack(f"[PalantirAIP][경고] 태스크 '{task}' 3회 연속 실패. Planner가 재계획 시도.")
                            replanned = self.planner.process(f"이 태스크를 더 세분화해서 다시 계획: {task}", state=planner_ctx)
                        print(f"[Planner] 재계획 결과: {replanned}")
                        state.history.append(f"[Planner] 재계획 결과: {replanned}")
                        state.plan = state.plan[:state.current_task_idx] + replanned + state.plan[state.current_task_idx+1:]
                        fail_loop = 0
                        task = state.plan[state.current_task_idx]
                            dev_result = self.developer.process([task], state=dev_ctx)
                            review = self.reviewer.process(dev_result, state=reviewer_ctx)
                        continue
                    print(f"[Reviewer] 테스트 실패, SelfImprover로 개선 시도 (시도 {fail_loop+1}/3)")
                    state.history.append(f"[Reviewer] 테스트 실패, SelfImprover로 개선 시도 (시도 {fail_loop+1}/3)")
                        # --- Iterative Debate(반복 토론/합의) 패턴 스텁 ---
                    need_improve = [r for r in review if '개선' in r.get('feedback','') or '문제' in r.get('feedback','') or '테스트 실패' in r.get('test_result','')]
                        # --- SelfImprover 컨텍스트 병합 및 주입 ---
                        improver_ctx = self.context_manager.merge_contexts("SelfImprover")
                        improvement = self.self_improver.process(need_improve if need_improve else review, state=improver_ctx)
            print(f"[SelfImprover] 자가개선 결과: {improvement}")
                    state.history.append(f"[SelfImprover] 자가개선 결과: {improvement}")
                    task_state.improvement_history.append(improvement)
                        self.context_manager.update_agent_context("SelfImprover", "last_improvement", improvement)
                        review = self.reviewer.process(dev_result, state=reviewer_ctx)
                    fail_loop += 1
                    task_state.fail_history.append(ImprovementHistory(improvement=improvement, fail_loop=fail_loop, review=review))
                    if fail_loop == 3 and not task_state.alert_sent:
                        notify_slack(f"[PalantirAIP][경고] 태스크 '{task}' 3회 연속 실패. 정책 위반/중단 필요.")
                        task_state.alert_sent = True
                        state.alerts.append({'task': task, 'fail_loop': fail_loop})
                        state.policy_triggered = True
                task_state.test_results.append(review)
                state.results.append(task_state)
                state.current_task_idx += 1
            print(f"[Orchestrator] 전체 태스크 완료. 결과: {state.results}")
            state.history.append(f"[Orchestrator] 전체 태스크 완료. 결과: {state.results}")
            return state.results
        except Exception as e:
            notify_slack(f"[PalantirAIP][오류] 오케스트레이터 예외 발생: {str(e)}")
            print(f"[오케스트레이터 오류] {str(e)}")
            if hasattr(state, 'history'):
                state.history.append(f"[오케스트레이터 오류] {str(e)}")
            return {"error": str(e)} 