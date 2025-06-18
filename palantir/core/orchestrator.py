"""개선된 멀티에이전트 오케스트레이션 시스템"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

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
from .shared_memory import SharedMemory
from .self_improver import SelfImprover
from .exceptions import OrchestratorError

logger = logging.getLogger(__name__)


class Orchestrator:
    """개선된 멀티에이전트 오케스트레이터"""

    def __init__(
        self,
        execution_mode: str = "parallel",
        max_concurrent_tasks: int = 5,
        task_timeout: int = 300,
        performance_threshold: float = 0.8,
    ):
        # 에이전트 초기화
        self.planner = PlannerAgent("Planner")
        self.developer = DeveloperAgent("Developer")
        self.reviewer = ReviewerAgent("Reviewer")
        self.self_improver = SelfImprovementAgent("SelfImprover")
        self.llm_mcp = LLMMCP()
        self.file_mcp = FileMCP()
        self.git_mcp = GitMCP()
        self.test_mcp = TestMCP()
        self.web_mcp = WebMCP()

        # 시스템 컴포넌트 초기화
        self.shared_memory = SharedMemory()
        self.context_manager = ContextManager()
        self.execution_mode = execution_mode
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_timeout = task_timeout
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)

        # 자기개선 시스템 초기화
        self.improvement_system = SelfImprover(
            shared_memory=self.shared_memory,
            context_manager=self.context_manager,
            performance_threshold=performance_threshold
        )

    async def _store_task_result(
        self,
        task_id: str,
        task: str,
        result: Any,
        agent: str,
        status: str = "success",
        error: Optional[str] = None,
    ):
        """작업 결과를 공유 메모리에 저장"""
        await self.shared_memory.store(
            key=f"task_result:{task_id}",
            value={
                "task": task,
                "result": result,
                "agent": agent,
                "status": status,
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
            },
            type="task_result",
            ttl=3600,  # 1시간 유지
            tags={agent, status, "task_result"},
            metadata={"task_id": task_id},
        )

    async def _process_task(self, task: str) -> TaskState:
        """단일 태스크 처리 (Developer → Reviewer → SelfImprover)"""
        task_id = str(uuid4())
        task_state = TaskState(task=task)

        try:
            async with self.semaphore:  # 동시 실행 제한
                # Developer 단계
                dev_ctx = self.context_manager.merge_contexts("Developer")
                dev_result = await self.developer.process([task], state=dev_ctx)
                await self._store_task_result(task_id, task, dev_result, "Developer")
                self.context_manager.update_agent_context(
                    "Developer", "last_result", dev_result
                )

                # Reviewer 단계
                reviewer_ctx = self.context_manager.merge_contexts("Reviewer")
                review = await self.reviewer.process(dev_result, state=reviewer_ctx)
                await self._store_task_result(task_id, task, review, "Reviewer")
                self.context_manager.update_agent_context(
                    "Reviewer", "last_review", review
                )

                # 테스트 실행 및 자가 개선 루프
                fail_loop = 0
                while any(
                    "테스트 실패" in r.get("test_result", "") for r in review
                ) and fail_loop < 3:
                    # 자기개선 시스템 실행
                    improvement_result = await self.improvement_system.run_improvement_cycle()
                    
                    if improvement_result["status"] == "success":
                        # 개선 사항이 있으면 적용
                        if "improvements" in improvement_result:
                            task_state.improvement_history.extend(
                                improvement_result["improvements"]
                            )
                    
                    # 개선된 상태에서 다시 리뷰
                    review = await self.reviewer.process(dev_result, state=reviewer_ctx)
                    fail_loop += 1

                if fail_loop >= 3:
                    logger.warning(f"Task '{task}' failed after 3 attempts")
                    task_state.alert_sent = True

                task_state.test_results.extend(review)
                return task_state

        except Exception as e:
            error_msg = f"Task processing error: {str(e)}"
            logger.error(error_msg)
            await self._store_task_result(
                task_id, task, None, "error", "failed", error_msg
            )
            raise OrchestratorError(error_msg)

    async def run(self, user_input: str) -> Dict[str, Any]:
        """사용자 입력에 대한 전체 오케스트레이션 실행"""
        try:
            logger.info(f"Starting orchestration for input: {user_input}")
            state = OrchestratorState(plan=[])
            state.history.append(f"[Planner] User request: {user_input}")

            # 계획 수립
            planner_ctx = self.context_manager.merge_contexts("Planner")
            plan = await self.planner.process(user_input, state=planner_ctx)
            logger.info(f"Task decomposition result: {plan}")
            state.history.append(f"[Planner] Task decomposition: {plan}")
            state.plan = plan

            # 태스크 실행 (병렬 또는 순차)
            if self.execution_mode == "parallel":
                tasks = [self._process_task(t) for t in plan]
                state.results = await asyncio.gather(*tasks, return_exceptions=True)
            else:
                for idx, task in enumerate(plan):
                    state.current_task_idx = idx
                    try:
                        result = await asyncio.wait_for(
                            self._process_task(task),
                            timeout=self.task_timeout
                        )
                        state.results.append(result)
                    except asyncio.TimeoutError:
                        logger.error(f"Task '{task}' timed out")
                        state.results.append(
                            TaskState(
                                task=task,
                                error="Task execution timed out",
                                alert_sent=True
                            )
                        )

            # 결과 저장 및 반환
            await self._store_task_result(
                str(uuid4()),
                "orchestration_complete",
                state.dict(),
                "Orchestrator"
            )

            # 전체 실행 후 자기개선 사이클 실행
            improvement_result = await self.improvement_system.run_improvement_cycle()
            if improvement_result["status"] == "success" and "improvements" in improvement_result:
                state.history.append(
                    f"[SelfImprover] Improvements applied: {len(improvement_result['improvements'])}"
                )

            logger.info("Orchestration completed successfully")
            return {
                "status": "success",
                "state": state.dict(),
                "improvements": improvement_result.get("improvements", [])
            }

        except Exception as e:
            error_msg = f"Orchestration error: {str(e)}"
            logger.error(error_msg)
            await self._store_task_result(
                str(uuid4()),
                "orchestration_error",
                {"error": str(e)},
                "Orchestrator",
                "failed",
                error_msg
            )
            raise OrchestratorError(error_msg)
