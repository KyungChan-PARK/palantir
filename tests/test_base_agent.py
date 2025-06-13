import pytest
from src.agents.base_agent import BaseAgent, AgentConfig

class TestAgent(BaseAgent):
    """테스트용 에이전트 구현"""
    
    async def process(self, input_data: str) -> str:
        return f"Processed: {input_data}"
    
    async def validate(self, output: str) -> bool:
        return isinstance(output, str) and output.startswith("Processed:")

@pytest.fixture
def agent_config():
    return AgentConfig(
        name="test_agent",
        description="Test agent for unit testing",
        model="gpt-4",
        system_prompt="You are a test agent."
    )

@pytest.fixture
def test_agent(agent_config):
    return TestAgent(agent_config)

@pytest.mark.asyncio
async def test_agent_execution(test_agent):
    result = await test_agent.execute("test input")
    assert result == "Processed: test input"

@pytest.mark.asyncio
async def test_agent_validation(test_agent):
    with pytest.raises(ValueError):
        await test_agent.execute(123)  # 잘못된 입력 타입

def test_agent_status(test_agent):
    status = test_agent.get_status()
    assert status["name"] == "test_agent"
    assert status["model"] == "gpt-4"
    assert "temperature" in status 