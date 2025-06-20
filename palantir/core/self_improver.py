"""자기개선 시스템 구현"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from .shared_memory import SharedMemory
from .context_manager import ContextManager
from .exceptions import SelfImprovementError
from .models.state import (
    ImprovementHistory,
    PerformanceMetrics,
    ImprovementSuggestion,
    ImprovementResult
)
from ..services.mcp.test_mcp import TestMCP

logger = logging.getLogger(__name__)


class SelfImprover:
    """자기개선 시스템"""

    def __init__(
        self,
        shared_memory: SharedMemory,
        context_manager: ContextManager,
        performance_threshold: float = 0.8
    ):
        """
        Args:
            shared_memory: 공유 메모리 인스턴스
            context_manager: 컨텍스트 매니저 인스턴스
            performance_threshold: 성능 임계값 (0-1 사이 값)
        """
        self.shared_memory = shared_memory
        self.context_manager = context_manager
        self.performance_threshold = performance_threshold
        self.test_mcp = TestMCP()

    async def analyze_performance(self) -> PerformanceMetrics:
        """현재 성능 분석

        Returns:
            PerformanceMetrics: 성능 지표
        """
        try:
            # 최근 작업 결과 조회
            task_results = await self.shared_memory.search(
                type="task_result",
                tags={"task_result"},
                limit=10
            )

            if not task_results:
                return PerformanceMetrics(
                    response_time=0.0,
                    accuracy=1.0,
                    memory_usage=0,
                    error_rate=0.0,
                    test_coverage=1.0
                )

            # 성능 지표 계산
            total_time = 0.0
            total_memory = 0
            error_count = 0
            success_count = 0

            for result in task_results:
                if result["status"] == "success":
                    success_count += 1
                    if result["processing_time"]:
                        total_time += result["processing_time"]
                    if result["memory_usage"]:
                        total_memory += result["memory_usage"]
                else:
                    error_count += 1

            total_count = len(task_results)
            avg_time = total_time / success_count if success_count > 0 else 0
            avg_memory = total_memory / success_count if success_count > 0 else 0
            accuracy = success_count / total_count if total_count > 0 else 1.0
            error_rate = error_count / total_count if total_count > 0 else 0.0

            # 테스트 커버리지 조회
            test_results = self.test_mcp.get_coverage()
            test_coverage = test_results.get("coverage", 1.0)

            return PerformanceMetrics(
                response_time=avg_time,
                accuracy=accuracy,
                memory_usage=avg_memory,
                error_rate=error_rate,
                test_coverage=test_coverage
            )

        except Exception as e:
            logger.error(f"성능 분석 중 오류 발생: {str(e)}")
            raise SelfImprovementError(f"성능 분석 실패: {str(e)}")

    async def generate_improvements(
        self,
        metrics: PerformanceMetrics
    ) -> List[ImprovementSuggestion]:
        """성능 지표를 기반으로 개선 사항 생성

        Args:
            metrics: 현재 성능 지표

        Returns:
            List[ImprovementSuggestion]: 개선 제안 목록
        """
        suggestions = []

        # 응답 시간 개선
        if metrics.response_time > 1.0:  # 목표: 1초 이하
            suggestions.append(
                ImprovementSuggestion(
                    target="code",
                    component="task_processing",
                    current_state=f"현재 응답 시간: {metrics.response_time:.2f}초",
                    suggested_change="작업 병렬 처리 도입",
                    reason="응답 시간이 목표치를 초과",
                    priority=1,
                    estimated_impact={"response_time": -0.5}
                )
            )

        # 정확도 개선
        if metrics.accuracy < 0.95:  # 목표: 95% 이상
            suggestions.append(
                ImprovementSuggestion(
                    target="model",
                    component="task_executor",
                    current_state=f"현재 정확도: {metrics.accuracy:.2%}",
                    suggested_change="모델 파라미터 최적화",
                    reason="정확도가 목표치에 미달",
                    priority=2,
                    estimated_impact={"accuracy": 0.1}
                )
            )

        # 메모리 사용량 개선
        if metrics.memory_usage > 1024:  # 목표: 1GB 이하
            suggestions.append(
                ImprovementSuggestion(
                    target="code",
                    component="memory_management",
                    current_state=f"현재 메모리 사용량: {metrics.memory_usage}MB",
                    suggested_change="메모리 캐시 최적화",
                    reason="메모리 사용량이 목표치를 초과",
                    priority=3,
                    estimated_impact={"memory_usage": -256}
                )
            )

        # 에러율 개선
        if metrics.error_rate > 0.05:  # 목표: 5% 이하
            suggestions.append(
                ImprovementSuggestion(
                    target="code",
                    component="error_handling",
                    current_state=f"현재 에러율: {metrics.error_rate:.2%}",
                    suggested_change="에러 처리 로직 강화",
                    reason="에러율이 목표치를 초과",
                    priority=1,
                    estimated_impact={"error_rate": -0.03}
                )
            )

        # 테스트 커버리지 개선
        if metrics.test_coverage < 0.9:  # 목표: 90% 이상
            suggestions.append(
                ImprovementSuggestion(
                    target="test",
                    component="test_coverage",
                    current_state=f"현재 테스트 커버리지: {metrics.test_coverage:.2%}",
                    suggested_change="테스트 케이스 추가",
                    reason="테스트 커버리지가 목표치에 미달",
                    priority=2,
                    estimated_impact={"test_coverage": 0.1}
                )
            )

        return suggestions

    async def apply_improvements(
        self,
        suggestions: List[ImprovementSuggestion]
    ) -> List[ImprovementResult]:
        """개선 사항을 적용하고 결과를 반환

        Args:
            suggestions: 적용할 개선 제안 목록

        Returns:
            List[ImprovementResult]: 개선 적용 결과 목록
        """
        results = []
        for suggestion in suggestions:
            try:
                # 개선 사항 적용 전 성능 측정
                before_metrics = await self.analyze_performance()

                # 개선 사항 적용
                await self._apply_single_improvement(suggestion)

                # 개선 사항 적용 후 성능 측정
                after_metrics = await self.analyze_performance()

                # 테스트 실행
                test_results = self.test_mcp.run_tests()
                test_success = all(result["success"] for result in test_results)

                if test_success:
                    # 개선 이력 저장
                    history = ImprovementHistory(
                        component=suggestion.component,
                        change_type=suggestion.target,
                        description=suggestion.suggested_change,
                        metrics_before=before_metrics.dict(),
                        metrics_after=after_metrics.dict(),
                        success=True
                    )
                    await self.shared_memory.store(
                        key=f"improvement:{datetime.now().isoformat()}",
                        value=history.dict(),
                        type="improvement_history",
                        tags={"improvement_cycle", suggestion.target},
                        ttl=86400 * 30  # 30일 보관
                    )

                    results.append(
                        ImprovementResult(
                            improvement=suggestion.dict(),
                            review="개선 사항이 성공적으로 적용됨",
                            test_results=test_results
                        )
                    )
                else:
                    # 테스트 실패 시 롤백
                    await self._rollback_improvement(suggestion)
                    results.append(
                        ImprovementResult(
                            improvement=suggestion.dict(),
                            fail_loop=1,
                            review="테스트 실패로 롤백됨",
                            test_results=test_results
                        )
                    )

            except Exception as e:
                logger.error(f"개선 사항 적용 중 오류 발생: {str(e)}")
                results.append(
                    ImprovementResult(
                        improvement=suggestion.dict(),
                        fail_loop=1,
                        review=f"개선 사항 적용 실패: {str(e)}"
                    )
                )

        return results

    async def run_improvement_cycle(self) -> Dict:
        """전체 개선 사이클 실행

        Returns:
            Dict: 개선 사이클 실행 결과
        """
        try:
            # 1. 현재 성능 분석
            metrics = await self.analyze_performance()
            logger.info(f"현재 성능 지표: {metrics}")

            # 2. 성능이 충분히 좋은지 확인
            if self._is_performance_satisfactory(metrics):
                return {
                    "status": "success",
                    "message": "현재 성능이 목표치를 충족",
                    "metrics": metrics.dict()
                }

            # 3. 개선 사항 생성
            suggestions = await self.generate_improvements(metrics)
            if not suggestions:
                return {
                    "status": "success",
                    "message": "개선이 필요한 사항이 없음",
                    "metrics": metrics.dict()
                }

            # 4. 개선 사항 적용
            results = await self.apply_improvements(suggestions)

            return {
                "status": "success",
                "metrics": metrics.dict(),
                "improvements": [r.dict() for r in results]
            }

        except Exception as e:
            logger.error(f"개선 사이클 실행 중 오류 발생: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def _is_performance_satisfactory(self, metrics: PerformanceMetrics) -> bool:
        """성능이 목표치를 충족하는지 확인

        Args:
            metrics: 현재 성능 지표

        Returns:
            bool: 성능 충족 여부
        """
        return all([
            metrics.response_time <= 1.0,
            metrics.accuracy >= 0.95,
            metrics.memory_usage <= 1024,
            metrics.error_rate <= 0.05,
            metrics.test_coverage >= 0.9
        ])

    async def _apply_single_improvement(self, suggestion: ImprovementSuggestion):
        """단일 개선 사항 적용

        Args:
            suggestion: 적용할 개선 제안
        """
        # TODO: 실제 개선 사항 적용 로직 구현
        await asyncio.sleep(0.1)  # 임시 구현

    async def _rollback_improvement(self, suggestion: ImprovementSuggestion):
        """개선 사항 롤백

        Args:
            suggestion: 롤백할 개선 제안
        """
        # TODO: 실제 롤백 로직 구현
        await asyncio.sleep(0.1)  # 임시 구현 