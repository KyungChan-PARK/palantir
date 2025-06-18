"""자기개선 시스템 통합 테스트"""

import pytest
import asyncio
from datetime import datetime

from palantir.core.self_improver import SelfImprover
from palantir.core.shared_memory import SharedMemory
from palantir.core.context_manager import ContextManager
from palantir.core.exceptions import SelfImprovementError


@pytest.fixture
async def shared_memory():
    """실제 Redis 기반 공유 메모리"""
    memory = SharedMemory()
    yield memory
    # 테스트 후 정리
    await memory.clear_all()


@pytest.fixture
def context_manager():
    """실제 컨텍스트 매니저"""
    return ContextManager()


@pytest.fixture
async def self_improver(shared_memory, context_manager):
    """테스트용 SelfImprover 인스턴스"""
    improver = SelfImprover(
        shared_memory=shared_memory,
        context_manager=context_manager,
        performance_threshold=0.8
    )
    return improver


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
    async def test_concurrent_improvement_cycles(self, self_improver, shared_memory):
        """동시 실행 테스트"""
        # 1. 테스트 데이터 준비
        test_task = {
            "task": "concurrent_test",
            "status": "success",
            "processing_time": 1.0,
            "memory_usage": 1000,
            "error": None
        }

        await shared_memory.store(
            key="task_result:concurrent",
            value=test_task,
            type="task_result",
            tags={"task_result", "success"},
            ttl=3600
        )

        # 2. 동시 실행
        cycles = 3
        tasks = [self_improver.run_improvement_cycle() for _ in range(cycles)]
        results = await asyncio.gather(*tasks)

        # 3. 결과 검증
        assert len(results) == cycles
        for result in results:
            assert result["status"] == "success"
            assert "metrics" in result

        # 4. 저장된 개선 이력 검증
        history = await shared_memory.search_by_tags(
            tags={"improvement_cycle"},
            match_all=True
        )
        assert len(history) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(self, self_improver, shared_memory):
        """에러 복구 테스트"""
        # 1. 잘못된 데이터 저장
        await shared_memory.store(
            key="task_result:invalid",
            value={"invalid": "data"},
            type="task_result",
            tags={"task_result"},
            ttl=3600
        )

        # 2. 개선 사이클 실행
        try:
            result = await self_improver.run_improvement_cycle()
            assert result["status"] == "success"
        except SelfImprovementError as e:
            # 에러가 발생해도 시스템이 계속 동작할 수 있어야 함
            assert str(e)

        # 3. 올바른 데이터로 재시도
        valid_task = {
            "task": "recovery_test",
            "status": "success",
            "processing_time": 0.5,
            "memory_usage": 500,
            "error": None
        }

        await shared_memory.store(
            key="task_result:valid",
            value=valid_task,
            type="task_result",
            tags={"task_result", "success"},
            ttl=3600
        )

        result = await self_improver.run_improvement_cycle()
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_performance_threshold(self, self_improver, shared_memory):
        """성능 임계값 테스트"""
        # 1. 좋은 성능의 테스트 데이터 준비
        good_task = {
            "task": "threshold_test",
            "status": "success",
            "processing_time": 0.1,
            "memory_usage": 100,
            "error": None
        }

        await shared_memory.store(
            key="task_result:good",
            value=good_task,
            type="task_result",
            tags={"task_result", "success"},
            ttl=3600
        )

        # 2. 개선 사이클 실행
        result = await self_improver.run_improvement_cycle()

        # 3. 결과 검증
        assert result["status"] == "success"
        assert result["message"] == "현재 성능이 목표치를 충족"
        assert "improvements" not in result  # 개선이 필요하지 않아야 함 