import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from src.data.pipeline import DataPipeline, DataConfig

@pytest.fixture
def temp_dir():
    """임시 디렉토리 생성"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def pipeline(temp_dir):
    """데이터 파이프라인 인스턴스 생성"""
    config = DataConfig(
        input_path=str(Path(temp_dir) / "input"),
        output_path=str(Path(temp_dir) / "output"),
        db_path=str(Path(temp_dir) / "test.db")
    )
    pipeline = DataPipeline(config)
    yield pipeline
    pipeline.close()

def test_process_data(pipeline):
    """데이터 전처리 테스트"""
    # 테스트 데이터 생성
    data = pd.DataFrame({
        'A': [1, 2, np.nan, 4, 5, 100],  # 이상치 포함
        'B': [1, 2, 3, 4, 5, 6]
    })
    
    # 데이터 처리
    processed_data = pipeline.process_data(data)
    
    # 검증
    assert len(processed_data) < len(data)  # 이상치가 제거되었는지 확인
    assert not processed_data['A'].isna().any()  # 결측치가 처리되었는지 확인

def test_save_to_parquet(pipeline):
    """Parquet 저장 테스트"""
    # 테스트 데이터 생성
    data = pd.DataFrame({
        'A': [1, 2, 3],
        'B': ['a', 'b', 'c']
    })
    
    # 데이터 저장
    pipeline.save_to_parquet(data, 'test')
    
    # 저장된 파일 확인
    output_path = Path(pipeline.config.output_path) / 'test.parquet'
    assert output_path.exists()
    
    # 데이터 로드 및 검증
    loaded_data = pd.read_parquet(output_path)
    pd.testing.assert_frame_equal(data, loaded_data)

def test_log_agent_action(pipeline):
    """에이전트 액션 로깅 테스트"""
    # 로그 데이터
    agent_id = "test_agent"
    action = "test_action"
    input_data = {"input": "test"}
    output_data = {"output": "result"}
    status = "success"
    
    # 로그 기록
    pipeline.log_agent_action(
        agent_id=agent_id,
        action=action,
        input_data=input_data,
        output_data=output_data,
        status=status
    )
    
    # 로그 조회 및 검증
    logs = pipeline.get_agent_logs(agent_id=agent_id)
    assert len(logs) == 1
    assert logs.iloc[0]['agent_id'] == agent_id
    assert logs.iloc[0]['action'] == action
    assert logs.iloc[0]['status'] == status

def test_log_performance_metrics(pipeline):
    """성능 메트릭 로깅 테스트"""
    # 메트릭 데이터
    cpu_usage = 50.0
    memory_usage = 60.0
    active_agents = 5
    total_requests = 100
    
    # 메트릭 기록
    pipeline.log_performance_metrics(
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        active_agents=active_agents,
        total_requests=total_requests
    )
    
    # 메트릭 조회 및 검증
    metrics = pipeline.get_performance_metrics()
    assert len(metrics) == 1
    assert metrics.iloc[0]['cpu_usage'] == cpu_usage
    assert metrics.iloc[0]['memory_usage'] == memory_usage
    assert metrics.iloc[0]['active_agents'] == active_agents
    assert metrics.iloc[0]['total_requests'] == total_requests

def test_get_agent_logs_with_date_range(pipeline):
    """날짜 범위로 에이전트 로그 조회 테스트"""
    # 테스트 데이터 생성
    now = datetime.now()
    agent_id = "test_agent"
    
    # 과거 로그
    pipeline.log_agent_action(
        agent_id=agent_id,
        action="old_action",
        input_data={},
        output_data={},
        status="success"
    )
    
    # 현재 로그
    pipeline.log_agent_action(
        agent_id=agent_id,
        action="new_action",
        input_data={},
        output_data={},
        status="success"
    )
    
    # 날짜 범위로 조회
    start_date = now - timedelta(hours=1)
    logs = pipeline.get_agent_logs(
        agent_id=agent_id,
        start_date=start_date
    )
    
    assert len(logs) == 1
    assert logs.iloc[0]['action'] == "new_action" 