import asyncio
from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch

from palantir.core.state import StateStore
from palantir.core.task_manager import Task, TaskManager, AgentTaskManager


@pytest.fixture
def state_store():
    return MagicMock(spec=StateStore)


@pytest.fixture
def task_manager(state_store):
    manager = TaskManager(state_store, max_workers=2, task_timeout=5)
    return manager


@pytest.fixture
def agent_task_manager(state_store):
    async def process_func(payload):
        return {"processed": payload}
    
    manager = AgentTaskManager(
        state_store,
        process_func,
        max_workers=2,
        task_timeout=5,
    )
    return manager


def test_task_creation():
    """작업 생성 테스트"""
    task = Task(task_id="test-1", payload={"data": "test"}, priority=1)
    assert task.task_id == "test-1"
    assert task.payload == {"data": "test"}
    assert task.priority == 1
    assert task.status == "pending"
    assert isinstance(task.created_at, datetime)


def test_task_to_dict():
    """작업 직렬화 테스트"""
    task = Task(task_id="test-1", payload={"data": "test"})
    data = task.to_dict()
    assert data["task_id"] == "test-1"
    assert data["payload"] == {"data": "test"}
    assert data["status"] == "pending"
    assert "created_at" in data


@pytest.mark.asyncio
async def test_task_manager_submit(task_manager):
    """작업 제출 테스트"""
    task_id = await task_manager.submit_task({"data": "test"})
    assert task_id in task_manager.tasks
    assert task_manager.tasks[task_id].status == "pending"


@pytest.mark.asyncio
async def test_task_manager_get_status(task_manager):
    """작업 상태 조회 테스트"""
    task_id = await task_manager.submit_task({"data": "test"})
    status = await task_manager.get_task_status(task_id)
    assert status["task_id"] == task_id
    assert status["status"] == "pending"


@pytest.mark.asyncio
async def test_task_manager_cancel(task_manager):
    """작업 취소 테스트"""
    task_id = await task_manager.submit_task({"data": "test"})
    success = await task_manager.cancel_task(task_id)
    assert success is True
    status = await task_manager.get_task_status(task_id)
    assert status["status"] == "cancelled"


@pytest.mark.asyncio
async def test_task_manager_stats(task_manager):
    """작업 관리자 통계 테스트"""
    await task_manager.submit_task({"data": "test1"})
    await task_manager.submit_task({"data": "test2"})
    
    stats = task_manager.get_stats()
    assert stats["total_tasks"] == 2
    assert stats["pending_tasks"] == 2
    assert stats["active_tasks"] == 0


@pytest.mark.asyncio
async def test_agent_task_manager_processing(agent_task_manager):
    """에이전트 작업 처리 테스트"""
    # 작업 관리자 시작
    await agent_task_manager.start()
    
    try:
        # 작업 제출
        task_id = await agent_task_manager.submit_task({"data": "test"})
        
        # 작업 완료 대기
        while True:
            status = await agent_task_manager.get_task_status(task_id)
            if status["status"] in ["completed", "failed", "timeout"]:
                break
            await asyncio.sleep(0.1)
        
        # 결과 확인
        assert status["status"] == "completed"
        assert status["result"] == {"processed": {"data": "test"}}
        
    finally:
        # 작업 관리자 중지
        await agent_task_manager.stop()


@pytest.mark.asyncio
async def test_task_timeout(agent_task_manager):
    """작업 타임아웃 테스트"""
    async def slow_process(_):
        await asyncio.sleep(10)
        return {"result": "too late"}
    
    agent_task_manager.process_func = slow_process
    await agent_task_manager.start()
    
    try:
        task_id = await agent_task_manager.submit_task({"data": "test"})
        
        while True:
            status = await agent_task_manager.get_task_status(task_id)
            if status["status"] in ["completed", "failed", "timeout"]:
                break
            await asyncio.sleep(0.1)
        
        assert status["status"] == "timeout"
        
    finally:
        await agent_task_manager.stop()


@pytest.mark.asyncio
async def test_task_priority(agent_task_manager):
    """작업 우선순위 테스트"""
    results = []
    
    async def ordered_process(payload):
        results.append(payload["order"])
        await asyncio.sleep(0.1)
        return {"processed": payload}
    
    agent_task_manager.process_func = ordered_process
    await agent_task_manager.start()
    
    try:
        # 낮은 우선순위 작업 먼저 제출
        await agent_task_manager.submit_task(
            {"order": 2},
            priority=10,
        )
        
        # 높은 우선순위 작업 나중에 제출
        await agent_task_manager.submit_task(
            {"order": 1},
            priority=1,
        )
        
        # 작업 완료 대기
        while len(results) < 2:
            await asyncio.sleep(0.1)
        
        # 높은 우선순위 작업이 먼저 처리되었는지 확인
        assert results[0] == 1
        assert results[1] == 2
        
    finally:
        await agent_task_manager.stop()


@pytest.mark.asyncio
async def test_concurrent_processing(agent_task_manager):
    """동시 처리 테스트"""
    processing = set()
    max_concurrent = 0
    
    async def concurrent_process(payload):
        processing.add(payload["id"])
        nonlocal max_concurrent
        max_concurrent = max(max_concurrent, len(processing))
        await asyncio.sleep(0.2)
        processing.remove(payload["id"])
        return {"processed": payload}
    
    agent_task_manager.process_func = concurrent_process
    await agent_task_manager.start()
    
    try:
        # 여러 작업 동시 제출
        task_ids = []
        for i in range(5):
            task_id = await agent_task_manager.submit_task({"id": i})
            task_ids.append(task_id)
        
        # 모든 작업 완료 대기
        for task_id in task_ids:
            while True:
                status = await agent_task_manager.get_task_status(task_id)
                if status["status"] == "completed":
                    break
                await asyncio.sleep(0.1)
        
        # 최대 2개의 작업이 동시에 처리되었는지 확인
        assert max_concurrent == 2
        
    finally:
        await agent_task_manager.stop() 