"""
에이전트 테스트
"""

from unittest.mock import Mock, patch

import pytest

from palantir.core.agents.developer import DeveloperAgent
from palantir.core.agents.planner import PlannerAgent
from palantir.core.agents.reviewer import ReviewerAgent
from palantir.core.agents.self_improver import SelfImprovementAgent
from palantir.core.exceptions import AgentError


@pytest.mark.unit
@pytest.mark.agent
class TestPlannerAgent:
    """PlannerAgent 테스트"""

    @pytest.fixture
    def planner(self, mock_agent_config, mock_mcp_config):
        """테스트용 PlannerAgent 인스턴스를 생성합니다."""
        config = mock_agent_config.copy()
        config["type"] = "planner"
        return PlannerAgent(config=config, mcp_config=mock_mcp_config)

    @pytest.mark.asyncio
    async def test_analyze_task(self, planner, mock_llm_response):
        """작업 분석 테스트"""
        with patch("palantir.services.mcp.llm.LLM_MCP.generate") as mock_generate:
            mock_generate.return_value = mock_llm_response
            analysis = await planner.analyze_task("테스트 작업")
            assert analysis is not None
            mock_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_subtasks(self, planner, mock_llm_response):
        """서브태스크 생성 테스트"""
        with patch("palantir.services.mcp.llm.LLM_MCP.generate") as mock_generate:
            mock_generate.return_value = mock_llm_response
            subtasks = await planner.create_subtasks("테스트 작업")
            assert isinstance(subtasks, list)
            mock_generate.assert_called_once()


@pytest.mark.unit
@pytest.mark.agent
class TestDeveloperAgent:
    """DeveloperAgent 테스트"""

    @pytest.fixture
    def developer(self, mock_agent_config, mock_mcp_config):
        """테스트용 DeveloperAgent 인스턴스를 생성합니다."""
        config = mock_agent_config.copy()
        config["type"] = "developer"
        return DeveloperAgent(config=config, mcp_config=mock_mcp_config)

    @pytest.mark.asyncio
    async def test_implement_feature(self, developer, mock_llm_response):
        """기능 구현 테스트"""
        with patch("palantir.services.mcp.llm.LLM_MCP.generate") as mock_generate:
            mock_generate.return_value = mock_llm_response
            result = await developer.implement_feature("테스트 기능")
            assert result is not None
            mock_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_tests(self, developer, mock_llm_response):
        """테스트 작성 테스트"""
        with patch("palantir.services.mcp.llm.LLM_MCP.generate") as mock_generate:
            mock_generate.return_value = mock_llm_response
            tests = await developer.write_tests("테스트 대상 코드")
            assert tests is not None
            mock_generate.assert_called_once()


@pytest.mark.unit
@pytest.mark.agent
class TestReviewerAgent:
    """ReviewerAgent 테스트"""

    @pytest.fixture
    def reviewer(self, mock_agent_config, mock_mcp_config):
        """테스트용 ReviewerAgent 인스턴스를 생성합니다."""
        config = mock_agent_config.copy()
        config["type"] = "reviewer"
        return ReviewerAgent(config=config, mcp_config=mock_mcp_config)

    @pytest.mark.asyncio
    async def test_review_code(self, reviewer, mock_llm_response):
        """코드 리뷰 테스트"""
        with patch("palantir.services.mcp.llm.LLM_MCP.generate") as mock_generate:
            mock_generate.return_value = mock_llm_response
            review = await reviewer.review_code("테스트 코드")
            assert review is not None
            mock_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_security(self, reviewer, mock_llm_response):
        """보안 검사 테스트"""
        with patch("palantir.services.mcp.llm.LLM_MCP.generate") as mock_generate:
            mock_generate.return_value = mock_llm_response
            security_report = await reviewer.check_security("테스트 코드")
            assert security_report is not None
            mock_generate.assert_called_once()


@pytest.mark.unit
@pytest.mark.agent
class TestSelfImprovementAgent:
    """SelfImprovementAgent 테스트"""

    @pytest.fixture
    def improver(self, mock_agent_config, mock_mcp_config):
        """테스트용 SelfImprovementAgent 인스턴스를 생성합니다."""
        config = mock_agent_config.copy()
        config["type"] = "self_improver"
        return SelfImprovementAgent(config=config, mcp_config=mock_mcp_config)

    @pytest.mark.asyncio
    async def test_analyze_performance(self, improver, mock_llm_response):
        """성능 분석 테스트"""
        with patch("palantir.services.mcp.llm.LLM_MCP.generate") as mock_generate:
            mock_generate.return_value = mock_llm_response
            analysis = await improver.analyze_performance(
                {"accuracy": 0.95, "latency": 100, "memory": 512}
            )
            assert analysis is not None
            mock_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_optimize_prompts(self, improver, mock_llm_response):
        """프롬프트 최적화 테스트"""
        with patch("palantir.services.mcp.llm.LLM_MCP.generate") as mock_generate:
            mock_generate.return_value = mock_llm_response
            optimized = await improver.optimize_prompts(
                {"system": "기존 시스템 프롬프트", "user": "기존 사용자 프롬프트"}
            )
            assert optimized is not None
            mock_generate.assert_called_once()


@pytest.mark.integration
@pytest.mark.agent
class TestAgentIntegration:
    """에이전트 통합 테스트"""

    @pytest.fixture
    def agents(self, mock_agent_config, mock_mcp_config):
        """테스트용 에이전트 인스턴스들을 생성합니다."""
        planner = PlannerAgent(
            config={**mock_agent_config, "type": "planner"}, mcp_config=mock_mcp_config
        )
        developer = DeveloperAgent(
            config={**mock_agent_config, "type": "developer"},
            mcp_config=mock_mcp_config,
        )
        reviewer = ReviewerAgent(
            config={**mock_agent_config, "type": "reviewer"}, mcp_config=mock_mcp_config
        )
        improver = SelfImprovementAgent(
            config={**mock_agent_config, "type": "self_improver"},
            mcp_config=mock_mcp_config,
        )
        return {
            "planner": planner,
            "developer": developer,
            "reviewer": reviewer,
            "improver": improver,
        }

    @pytest.mark.asyncio
    async def test_full_workflow(self, agents, mock_llm_response):
        """전체 워크플로우 테스트"""
        with patch("palantir.services.mcp.llm.LLM_MCP.generate") as mock_generate:
            mock_generate.return_value = mock_llm_response

            # 1. Planner가 작업 분석
            task = "새로운 기능 개발"
            analysis = await agents["planner"].analyze_task(task)
            assert analysis is not None

            # 2. Developer가 구현
            implementation = await agents["developer"].implement_feature(task)
            assert implementation is not None

            # 3. Reviewer가 검토
            review = await agents["reviewer"].review_code(implementation)
            assert review is not None

            # 4. SelfImprover가 개선
            metrics = {"accuracy": 0.95, "latency": 100, "memory": 512}
            improvement = await agents["improver"].analyze_performance(metrics)
            assert improvement is not None

    @pytest.mark.asyncio
    async def test_error_handling(self, agents):
        """에러 처리 테스트"""
        with patch("palantir.services.mcp.llm.LLM_MCP.generate") as mock_generate:
            mock_generate.side_effect = Exception("API 오류")

            with pytest.raises(AgentError):
                await agents["planner"].analyze_task("테스트 작업")

            with pytest.raises(AgentError):
                await agents["developer"].implement_feature("테스트 기능")

            with pytest.raises(AgentError):
                await agents["reviewer"].review_code("테스트 코드")

            with pytest.raises(AgentError):
                await agents["improver"].analyze_performance({})

    @pytest.mark.asyncio
    async def test_memory_sharing(self, agents, mock_llm_response):
        """메모리 공유 테스트"""
        with patch("palantir.services.mcp.llm.LLM_MCP.generate") as mock_generate:
            mock_generate.return_value = mock_llm_response

            # Planner가 메모리 저장
            agents["planner"].update_memory(
                "task_info", {"description": "테스트 작업", "priority": "high"}
            )

            # Developer가 메모리 접근
            task_info = agents["developer"].get_memory("task_info")
            assert task_info is not None
            assert task_info["description"] == "테스트 작업"

            # Reviewer가 메모리 업데이트
            task_info["status"] = "reviewed"
            agents["reviewer"].update_memory("task_info", task_info)

            # SelfImprover가 메모리 확인
            final_info = agents["improver"].get_memory("task_info")
            assert final_info["status"] == "reviewed"
