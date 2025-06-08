import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from palantir.core.action_executor import run_deployment

@pytest.mark.asyncio
async def test_run_deployment_success():
    mock_deployment = AsyncMock()
    mock_deployment.id = "deployment-123"
    mock_flow_run = AsyncMock()
    mock_flow_run.id = "flowrun-456"
    
    async def mock_get_client():
        class MockClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                pass
            async def read_deployment_by_name(self, name):
                assert name == "notify_user"
                return mock_deployment
            async def create_flow_run_from_deployment(self, deployment_id, parameters):
                assert deployment_id == "deployment-123"
                assert parameters == {"user_id": "u1", "message": "hi"}
                return mock_flow_run
        return MockClient()
    
    with patch("palantir.core.action_executor.get_client", mock_get_client):
        flow_run_id = await run_deployment("notify_user", {"user_id": "u1", "message": "hi"})
        assert flow_run_id == "flowrun-456" 