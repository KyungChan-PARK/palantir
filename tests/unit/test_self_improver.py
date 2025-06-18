"""자기개선 시스템 단위 테스트"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from palantir.core.self_improver import (
    SelfImprover,
    PerformanceMetrics,
    ImprovementSuggestion,
)
from palantir.core.exceptions import SelfImprovementError


@pytest.fixture
def mock_shared_memory():
    """공유 메모리 목업"""
    mock = AsyncMock()
    mock.search_by_tags = AsyncMock(return_value=[
        MagicMock(value={
            "status": "success",
            "processing_time": 0.5,
            "memory_usage": 256,
        })
    ])
    mock.store = AsyncMock()
    return mock


@pytest.fixture
def mock_context_manager():
    """컨텍스트 매니저 목업"""
    return MagicMock()


@pytest.fixture
def self_improver(mock_shared_memory, mock_context_manager):
    """테스트용 SelfImprover 인스턴스"""
    return SelfImprover(
        shared_memory=mock_shared_memory,
        context_manager=mock_context_manager,
        performance_threshold=0.8
    )


class TestSelfImprover:
    """SelfImprover 테스트 스위트"""

    @pytest.mark.asyncio
    async def test_analyze_performance(self, self_improver, mock_shared_memory):
        """성능 분석 테스트"""
        metrics = await self_improver.analyze_performance()
        
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.response_time == 0.5
        assert metrics.memory_usage == 256
        mock_shared_memory.search_by_tags.assert_called_once_with(
            tags={"task_result"},
            match_all=True
        )

    @pytest.mark.asyncio
    async def test_analyze_performance_no_data(self, self_improver, mock_shared_memory):
        """데이터가 없는 경우 성능 분석 테스트"""
        mock_shared_memory.search_by_tags.return_value = []
        metrics = await self_improver.analyze_performance()
        
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.response_time == 0.0
        assert metrics.accuracy == 0.0
        assert metrics.memory_usage == 0.0
        assert metrics.error_rate == 0.0
        assert metrics.test_coverage == 0.0

    @pytest.mark.asyncio
    async def test_generate_improvements(self, self_improver):
        """개선 제안 생성 테스트"""
        metrics = PerformanceMetrics(
            response_time=2.0,  # 목표: 1.0초 이하
            accuracy=0.8,       # 목표: 0.95 이상
            memory_usage=1500,  # 목표: 1024MB 이하
            error_rate=0.1,     # 목표: 0.05 이하
            test_coverage=0.7   # 목표: 0.9 이상
        )
        
        suggestions = await self_improver.generate_improvements(metrics)
        
        assert len(suggestions) == 5  # 모든 지표가 목표치를 벗어나므로 5개의 제안
        assert all(isinstance(s, ImprovementSuggestion) for s in suggestions)
        
        # 우선순위 검증
        priorities = [s.priority for s in suggestions]
        assert priorities == sorted(priorities)  # 우선순위 순으로 정렬되어 있어야 함

    @pytest.mark.asyncio
    async def test_apply_improvements(self, self_improver, mock_shared_memory):
        """개선 사항 적용 테스트"""
        suggestions = [
            ImprovementSuggestion(
                target="code",
                component="task_processing",
                current_state="현재 응답 시간: 2.0초",
                suggested_change="작업 병렬 처리 도입",
                reason="응답 시간이 목표치를 초과",
                priority=1,
                estimated_impact={"response_time": -0.5}
            )
        ]
        
        results = await self_improver.apply_improvements(suggestions)
        
        assert len(results) == 1
        assert results[0].improvement == suggestions[0].dict()
        assert results[0].fail_loop == 0
        mock_shared_memory.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_improvement_cycle(self, self_improver):
        """전체 개선 사이클 테스트"""
        with patch.object(self_improver, 'analyze_performance') as mock_analyze, \
             patch.object(self_improver, 'generate_improvements') as mock_generate, \
             patch.object(self_improver, 'apply_improvements') as mock_apply:
            
            # 성능이 목표치에 미달하는 상황 설정
            mock_analyze.return_value = PerformanceMetrics(
                response_time=2.0,
                accuracy=0.8,
                memory_usage=1500,
                error_rate=0.1,
                test_coverage=0.7
            )
            
            mock_generate.return_value = [
                ImprovementSuggestion(
                    target="code",
                    component="task_processing",
                    current_state="현재 응답 시간: 2.0초",
                    suggested_change="작업 병렬 처리 도입",
                    reason="응답 시간이 목표치를 초과",
                    priority=1,
                    estimated_impact={"response_time": -0.5}
                )
            ]
            
            mock_apply.return_value = [MagicMock()]
            
            result = await self_improver.run_improvement_cycle()
            
            assert result["status"] == "success"
            assert "improvements" in result
            mock_analyze.assert_called_once()
            mock_generate.assert_called_once()
            mock_apply.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_improvement_cycle_no_improvements_needed(self, self_improver):
        """개선이 필요없는 경우 테스트"""
        with patch.object(self_improver, 'analyze_performance') as mock_analyze:
            # 성능이 이미 충분히 좋은 상황 설정
            mock_analyze.return_value = PerformanceMetrics(
                response_time=0.5,
                accuracy=0.98,
                memory_usage=512,
                error_rate=0.01,
                test_coverage=0.95
            )
            
            result = await self_improver.run_improvement_cycle()
            
            assert result["status"] == "success"
            assert result["message"] == "현재 성능이 목표치를 충족"

    @pytest.mark.asyncio
    async def test_error_handling(self, self_improver, mock_shared_memory):
        """에러 처리 테스트"""
        mock_shared_memory.search_by_tags.side_effect = Exception("테스트 에러")
        
        with pytest.raises(SelfImprovementError):
            await self_improver.analyze_performance() 