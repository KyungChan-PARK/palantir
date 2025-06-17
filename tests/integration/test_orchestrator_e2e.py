import sys
import types
import pytest

sys.modules.setdefault('src.data.pipeline', types.ModuleType('pipeline'))
sys.modules['src.data.pipeline'].DataConfig = object
sys.modules['src.data.pipeline'].DataPipeline = object
sys.modules.setdefault('src.core.mcp', types.ModuleType('mcp'))
sys.modules['src.core.mcp'].MCP = object
sys.modules['src.core.mcp'].MCPConfig = object

from src.agents.base_agent import AgentConfig
from src.core.orchestrator import Orchestrator

@pytest.mark.asyncio
async def test_orchestrator_run():
    cfg = AgentConfig(name='a', description='a', model='gpt', system_prompt='x')
    orch = Orchestrator(cfg, cfg, cfg)
    result = await orch.run('test input')
    assert 'results' in result
    assert result['results']
