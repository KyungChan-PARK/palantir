"""
BaseAgent 테스트
"""
import pytest
from unittest.mock import Mock, patch
from palantir.core.agents.base import BaseAgent
from palantir.core.exceptions import AgentError, MCPError

@pytest.mark.unit
@pytest.mark.agent
class TestBaseAgent:
    """BaseAgent 테스트"""

    @pytest.fixture
    def agent(self, mock_agent_config, mock_mcp_config):
        """테스트용 BaseAgent 인스턴스를 생성합니다."""
        return BaseAgent(config=mock_agent_config, mcp_config=mock_mcp_config)

    def test_init(self, agent, mock_agent_config):
        """초기화 테스트"""
        assert agent.name == mock_agent_config["name"]
        assert agent.type == mock_agent_config["type"]
        assert agent.model == mock_agent_config["model"]
        assert agent.temperature == mock_agent_config["temperature"]
        assert agent.max_tokens == mock_agent_config["max_tokens"]

    @pytest.mark.asyncio
    async def test_think(self, agent, mock_llm_response):
        """think 메소드 테스트"""
        with patch("palantir.services.mcp.llm.LLM_MCP.generate") as mock_generate:
            mock_generate.return_value = mock_llm_response
            response = await agent.think("테스트 프롬프트")
            assert response == mock_llm_response["choices"][0]["text"]
            mock_generate.assert_called_once_with(
                prompt="테스트 프롬프트",
                model=agent.model,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens
            )

    @pytest.mark.asyncio
    async def test_think_error(self, agent):
        """think 메소드 에러 처리 테스트"""
        with patch("palantir.services.mcp.llm.LLM_MCP.generate") as mock_generate:
            mock_generate.side_effect = MCPError("LLM 오류")
            with pytest.raises(AgentError) as exc_info:
                await agent.think("테스트 프롬프트")
            assert "LLM 처리 중 오류 발생" in str(exc_info.value)

    def test_validate_config(self, mock_agent_config):
        """설정 유효성 검사 테스트"""
        # 유효한 설정
        BaseAgent.validate_config(mock_agent_config)

        # 필수 필드 누락
        invalid_config = mock_agent_config.copy()
        del invalid_config["name"]
        with pytest.raises(ValueError) as exc_info:
            BaseAgent.validate_config(invalid_config)
        assert "필수 설정 누락" in str(exc_info.value)

        # 잘못된 타입
        invalid_config = mock_agent_config.copy()
        invalid_config["temperature"] = "high"
        with pytest.raises(ValueError) as exc_info:
            BaseAgent.validate_config(invalid_config)
        assert "잘못된 설정 타입" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_tool(self, agent):
        """도구 실행 테스트"""
        mock_tool = Mock()
        mock_tool.return_value = "도구 실행 결과"
        
        result = await agent.execute_tool(
            tool_name="test_tool",
            tool_func=mock_tool,
            args={"arg1": "value1"}
        )
        
        assert result == "도구 실행 결과"
        mock_tool.assert_called_once_with(arg1="value1")

    @pytest.mark.asyncio
    async def test_execute_tool_error(self, agent):
        """도구 실행 에러 처리 테스트"""
        mock_tool = Mock()
        mock_tool.side_effect = Exception("도구 실행 오류")
        
        with pytest.raises(AgentError) as exc_info:
            await agent.execute_tool(
                tool_name="test_tool",
                tool_func=mock_tool,
                args={"arg1": "value1"}
            )
        assert "도구 실행 중 오류 발생" in str(exc_info.value)

    def test_get_memory(self, agent):
        """메모리 접근 테스트"""
        # 메모리 저장
        agent.memory["test_key"] = "test_value"
        
        # 메모리 조회
        assert agent.get_memory("test_key") == "test_value"
        
        # 존재하지 않는 키
        assert agent.get_memory("non_existent") is None
        
        # 기본값 설정
        assert agent.get_memory("non_existent", default="default") == "default"

    def test_update_memory(self, agent):
        """메모리 업데이트 테스트"""
        # 새로운 메모리 추가
        agent.update_memory("test_key", "test_value")
        assert agent.memory["test_key"] == "test_value"
        
        # 기존 메모리 업데이트
        agent.update_memory("test_key", "new_value")
        assert agent.memory["test_key"] == "new_value"

    def test_clear_memory(self, agent):
        """메모리 초기화 테스트"""
        # 메모리 설정
        agent.memory["test_key1"] = "test_value1"
        agent.memory["test_key2"] = "test_value2"
        
        # 메모리 초기화
        agent.clear_memory()
        assert len(agent.memory) == 0

    @pytest.mark.asyncio
    async def test_handle_error(self, agent):
        """에러 처리 테스트"""
        error = Exception("테스트 에러")
        
        # 기본 에러 처리
        with pytest.raises(AgentError) as exc_info:
            await agent.handle_error(error, "테스트 작업")
        assert "테스트 작업 중 오류 발생" in str(exc_info.value)
        
        # 커스텀 에러 처리
        custom_handler = Mock()
        agent.error_handlers[Exception] = custom_handler
        await agent.handle_error(error, "테스트 작업")
        custom_handler.assert_called_once_with(error)

    def test_process_abstract(self):
        """process 메서드가 추상 메서드인지 확인"""
        with pytest.raises(TypeError):
            BaseAgent("test_agent")

    def test_process(self):
        """process 메서드 테스트"""
        class TestAgent(BaseAgent):
            def process(self, input_data, state=None):
                return input_data
                
        agent = TestAgent("test_agent")
        assert agent.process("test_input") == "test_input" 