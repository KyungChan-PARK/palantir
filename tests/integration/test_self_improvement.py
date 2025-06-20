"""자기개선 시스템 통합 테스트"""

import pytest
from datetime import datetime

from palantir.core.self_improver import SelfImprover
from palantir.core.shared_memory import SharedMemory
from palantir.core.context_manager import ContextManager
from palantir.core.exceptions import SelfImprovementError


@pytest.fixture
async def shared_memory():
    """공유 메모리 픽스처"""
    memory = SharedMemory()
    yield memory
    await memory.clear()


@pytest.fixture
def context_manager():
    """컨텍스트 매니저 픽스처"""
    return ContextManager()


@pytest.fixture
def self_improver(shared_memory, context_manager):
    """자기개선 시스템 픽스처"""
    return SelfImprover(shared_memory, context_manager)


@pytest.mark.integration
class TestSelfImprovementIntegration:
    """자기개선 시스템 통합 테스트 스위트"""

    @pytest.mark.asyncio
    async def test_full_improvement_cycle(self, self_improver, shared_memory):
        """전체 개선 사이클 통합 테스트"""
        # 1. 테스트 데이터 준비
        test_tasks = [
            {
                "task": "task1",
                "status": "success",
                "processing_time": 1.5,
                "memory_usage": 1200,
                "error": None
            },
            {
                "task": "task2",
                "status": "error",
                "processing_time": None,
                "memory_usage": None,
                "error": "테스트 에러"
            },
            {
                "task": "task3",
                "status": "success",
                "processing_time": 0.8,
                "memory_usage": 800,
                "error": None
            }
        ]

        # 2. 테스트 데이터 저장
        for idx, task in enumerate(test_tasks):
            await shared_memory.store(
                key=f"task_result:{idx}",
                value=task,
                type="task_result",
                tags={"task_result", task["status"]},
                ttl=3600
            )

        # 3. 개선 사이클 실행
        result = await self_improver.run_improvement_cycle()

        # 4. 결과 검증
        assert result["status"] == "success"
        assert "metrics" in result
        metrics = result["metrics"]

        # 성능 지표 검증
        assert 0.0 <= metrics["accuracy"] <= 1.0
        assert metrics["response_time"] > 0
        assert metrics["memory_usage"] > 0
        assert 0.0 <= metrics["error_rate"] <= 1.0

        # 개선 제안 검증
        if "improvements" in result:
            improvements = result["improvements"]
            for improvement in improvements:
                assert "improvement" in improvement
                assert "fail_loop" in improvement
                assert "review" in improvement

    @pytest.mark.asyncio
    async def test_analyze_performance(self, self_improver, shared_memory):
        """성능 분석 테스트"""
        # 1. 테스트 데이터 저장
        await shared_memory.store(
            key="task_result:1",
            value={
                "status": "success",
                "processing_time": 1.0,
                "memory_usage": 500
            },
            type="task_result",
            tags={"task_result", "success"},
            ttl=3600
        )

        # 2. 성능 분석 실행
        metrics = await self_improver.analyze_performance()

        # 3. 결과 검증
        assert metrics.response_time == 1.0
        assert metrics.memory_usage == 500
        assert metrics.accuracy == 1.0
        assert metrics.error_rate == 0.0

    @pytest.mark.asyncio
    async def test_generate_improvements(self, self_improver):
        """개선 제안 생성 테스트"""
        # 1. 테스트 성능 지표 생성
        from palantir.core.models.state import PerformanceMetrics
        metrics = PerformanceMetrics(
            response_time=2.0,  # 목표: 1초 이하
            accuracy=0.8,  # 목표: 95% 이상
            memory_usage=1500,  # 목표: 1GB 이하
            error_rate=0.1,  # 목표: 5% 이하
            test_coverage=0.7  # 목표: 90% 이상
        )

        # 2. 개선 제안 생성
        suggestions = await self_improver.generate_improvements(metrics)

        # 3. 결과 검증
        assert len(suggestions) == 5  # 모든 지표가 목표에 미달하므로 5개의 제안이 생성되어야 함
        for suggestion in suggestions:
            assert suggestion.target in ["code", "model", "test"]
            assert suggestion.priority >= 1 and suggestion.priority <= 5
            assert suggestion.estimated_impact is not None

    @pytest.mark.asyncio
    async def test_apply_improvements(self, self_improver):
        """개선 사항 적용 테스트"""
        # 1. 테스트 개선 제안 생성
        from palantir.core.models.state import ImprovementSuggestion
        suggestion = ImprovementSuggestion(
            target="code",
            component="task_processing",
            current_state="현재 응답 시간: 2.0초",
            suggested_change="작업 병렬 처리 도입",
            reason="응답 시간이 목표치를 초과",
            priority=1,
            estimated_impact={"response_time": -0.5}
        )

        # 2. 개선 사항 적용
        results = await self_improver.apply_improvements([suggestion])

        # 3. 결과 검증
        assert len(results) == 1
        result = results[0]
        assert result.improvement == suggestion.dict()
        assert result.fail_loop >= 0
        assert result.review is not None 