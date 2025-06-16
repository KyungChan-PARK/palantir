import asyncio
import uuid
from typing import Dict, List

import pytest
from fastapi.testclient import TestClient

from palantir.core.agents.base import (AgentResult, AgentTask, DeveloperAgent,
                                     PlannerAgent, ReviewerAgent,
                                     SelfImproverAgent)
from palantir.main import app
from palantir.services.mcp.base import MCPContext, MCPResponse

client = TestClient(app)


@pytest.fixture
def planner():
    return PlannerAgent()


@pytest.fixture
def developer():
    return DeveloperAgent()


@pytest.fixture
def reviewer():
    return ReviewerAgent()


@pytest.fixture
def self_improver():
    return SelfImproverAgent()


async def create_sample_task(task_type: str, parameters: Dict) -> AgentTask:
    return AgentTask(
        type=task_type,
        description=f"Test {task_type} task",
        parameters=parameters
    )


@pytest.mark.asyncio
async def test_planner_workflow(planner: PlannerAgent):
    """Planner 워크플로우 테스트"""
    task = await create_sample_task("planning", {"goal": "Implement new feature"})
    result = await planner.process_task(task)
    
    assert result.status == "success"
    assert "subtasks" in result.result
    assert "plan" in result.result
    assert len(result.result["subtasks"]) > 0


@pytest.mark.asyncio
async def test_developer_workflow(developer: DeveloperAgent):
    """Developer 워크플로우 테스트"""
    task = await create_sample_task(
        "development",
        {
            "requirements": "Add new endpoint",
            "code_path": "api/endpoints.py"
        }
    )
    result = await developer.process_task(task)
    
    assert result.status == "success"
    assert "code_changes" in result.result
    assert "test_results" in result.result
    assert result.result["test_results"]["passed"]


@pytest.mark.asyncio
async def test_reviewer_workflow(reviewer: ReviewerAgent):
    """Reviewer 워크플로우 테스트"""
    task = await create_sample_task(
        "review",
        {
            "code_changes": {
                "files": ["api/endpoints.py"],
                "diff": "sample diff content"
            }
        }
    )
    result = await reviewer.process_task(task)
    
    assert result.status == "success"
    assert "review_results" in result.result
    assert "suggestions" in result.result
    assert isinstance(result.result["suggestions"], list)


@pytest.mark.asyncio
async def test_self_improver_workflow(self_improver: SelfImproverAgent):
    """SelfImprover 워크플로우 테스트"""
    task = await create_sample_task(
        "improvement",
        {
            "metrics": {
                "response_time": 200,
                "error_rate": 0.05
            }
        }
    )
    result = await self_improver.process_task(task)
    
    assert result.status == "success"
    assert "analysis" in result.result
    assert "improvements" in result.result
    assert isinstance(result.result["improvements"], list)


@pytest.mark.asyncio
async def test_end_to_end_workflow(
    planner: PlannerAgent,
    developer: DeveloperAgent,
    reviewer: ReviewerAgent,
    self_improver: SelfImproverAgent
):
    """전체 워크플로우 통합 테스트"""
    
    # 1. Planner: 태스크 분해 및 계획 수립
    planning_task = await create_sample_task(
        "planning",
        {"goal": "Implement new API endpoint"}
    )
    planning_result = await planner.process_task(planning_task)
    assert planning_result.status == "success"
    
    # 2. Developer: 코드 구현
    dev_task = await create_sample_task(
        "development",
        {
            "requirements": planning_result.result["subtasks"][0]["description"],
            "code_path": "api/new_endpoint.py"
        }
    )
    dev_result = await developer.process_task(dev_task)
    assert dev_result.status == "success"
    
    # 3. Reviewer: 코드 리뷰
    review_task = await create_sample_task(
        "review",
        {"code_changes": dev_result.result["code_changes"]}
    )
    review_result = await reviewer.process_task(review_task)
    assert review_result.status == "success"
    
    # 4. SelfImprover: 성능 분석 및 개선
    improve_task = await create_sample_task(
        "improvement",
        {
            "metrics": {
                "response_time": dev_result.result["test_results"].get("response_time", 150),
                "coverage": dev_result.result["test_results"].get("coverage", 85.5)
            }
        }
    )
    improve_result = await self_improver.process_task(improve_task)
    assert improve_result.status == "success"


def test_api_endpoints():
    """API 엔드포인트 테스트"""
    
    # 상태 확인
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json()["app"] == "ok"
    
    # 온톨로지 쿼리
    response = client.post(
        "/ontology/query",
        json={
            "type": "Product",
            "properties": {"category": "Electronics"}
        }
    )
    assert response.status_code == 200
    
    # 이벤트 생성
    response = client.post(
        "/ontology/events",
        json={
            "object_id": str(uuid.uuid4()),
            "event_type": "STOCK_UPDATE",
            "details": {"old_value": 100, "new_value": 95}
        }
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_mcp_integration():
    """MCP 통합 테스트"""
    
    # LLM 요청
    context = MCPContext(
        request_id=uuid.uuid4(),
        agent_id="test_agent",
        task_type="completion",
        parameters={
            "model": "gpt-4",
            "prompt": "Write a test function"
        }
    )
    
    # 파일 시스템 요청
    file_context = MCPContext(
        request_id=uuid.uuid4(),
        agent_id="test_agent",
        task_type="read",
        parameters={
            "path": "test_file.py"
        }
    )
    
    # TODO: MCP 핸들러 호출 및 응답 검증 구현 