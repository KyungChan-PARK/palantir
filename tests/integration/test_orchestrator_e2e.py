import sys
import types
import pytest
from fastapi.testclient import TestClient

sys.modules.setdefault('src.data.pipeline', types.ModuleType('pipeline'))
sys.modules['src.data.pipeline'].DataConfig = object
sys.modules['src.data.pipeline'].DataPipeline = object
sys.modules.setdefault('src.core.mcp', types.ModuleType('mcp'))
sys.modules['src.core.mcp'].MCP = object
sys.modules['src.core.mcp'].MCPConfig = object

from src.agents.base_agent import AgentConfig
from src.core.orchestrator import Orchestrator
from palantir.api.status import router

@pytest.mark.asyncio
async def test_orchestrator_run():
    cfg = AgentConfig(name='a', description='a', model='gpt', system_prompt='x')
    orch = Orchestrator(cfg, cfg, cfg)
    result = await orch.run('test input')
    assert 'results' in result
    assert result['results']
    # 상태 저장 확인
    assert hasattr(orch, 'state')
    assert orch.state == result

def test_orchestrator_history_api():
    client = TestClient(router)
    
    # 초기 상태 (오케스트레이터 없음)
    response = client.get("/orchestrator/history")
    assert response.status_code == 200
    assert response.json() == {
        "history": [],
        "state": None,
        "improvements": [],
        "rollbacked": [],
        "rollback_reasons": [],
        "policy_violations": []
    }
    
    # 오케스트레이터 실행
    response = client.post("/orchestrator/run", json="test input")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "success"
    
    # 실행 후 히스토리 확인
    response = client.get("/orchestrator/history")
    assert response.status_code == 200
    history = response.json()
    assert "history" in history
    assert "state" in history
    assert isinstance(history["improvements"], list)
    assert isinstance(history["rollbacked"], list)
    assert isinstance(history["rollback_reasons"], list)
    assert isinstance(history["policy_violations"], list)
