# FastAPI 엔드포인트 테스트 (YAML 유효성 검증)
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

VALID_YAML = """
name: test-pipeline
description: test
tasks:
  - id: t1
    type: python
    params:
      script: print('hi')
    depends_on: []
"""
INVALID_YAML = """
name: test-pipeline
description: test
tasks:
  - id: t1
    params: {}
"""


def test_pipeline_validate_success():
    res = client.post(
        "/pipeline/validate", files={"file": ("pipeline.yaml", VALID_YAML)}
    )
    assert res.status_code == 200
    assert res.json()["valid"] is True


def test_pipeline_validate_fail():
    res = client.post(
        "/pipeline/validate", files={"file": ("pipeline.yaml", INVALID_YAML)}
    )
    assert res.status_code == 200
    assert res.json()["valid"] is False


import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# DataPipeline 단위 테스트 (main)
import pytest

from src.data.pipeline import DataConfig, DataPipeline


@pytest.fixture
def temp_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def pipeline(temp_dir):
    config = DataConfig(
        input_path=str(Path(temp_dir) / "input"),
        output_path=str(Path(temp_dir) / "output"),
        db_path=str(Path(temp_dir) / "test.db"),
    )
    pipeline = DataPipeline(config)
    yield pipeline
    pipeline.close()


def test_process_data(pipeline):
    data = pd.DataFrame({"A": [1, 2, np.nan, 4, 5, 100], "B": [1, 2, 3, 4, 5, 6]})
    processed_data = pipeline.process_data(data)
    assert len(processed_data) < len(data)
    assert not processed_data["A"].isna().any()


def test_save_to_parquet(pipeline):
    data = pd.DataFrame({"A": [1, 2, 3], "B": ["a", "b", "c"]})
    pipeline.save_to_parquet(data, "test")
    output_path = Path(pipeline.config.output_path) / "test.parquet"
    assert output_path.exists()
    loaded_data = pd.read_parquet(output_path)
    pd.testing.assert_frame_equal(data, loaded_data)


def test_log_agent_action(pipeline):
    agent_id = "test_agent"
    action = "test_action"
    input_data = {"input": "test"}
    output_data = {"output": "result"}
    status = "success"
    pipeline.log_agent_action(
        agent_id=agent_id,
        action=action,
        input_data=input_data,
        output_data=output_data,
        status=status,
    )
    logs = pipeline.get_agent_logs(agent_id=agent_id)
    assert len(logs) == 1
    assert logs.iloc[0]["agent_id"] == agent_id
    assert logs.iloc[0]["action"] == action
    assert logs.iloc[0]["status"] == status


def test_log_performance_metrics(pipeline):
    cpu_usage = 50.0
    memory_usage = 60.0
    active_agents = 5
    total_requests = 100
    pipeline.log_performance_metrics(
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        active_agents=active_agents,
        total_requests=total_requests,
    )
    metrics = pipeline.get_performance_metrics()
    assert len(metrics) == 1
    assert metrics.iloc[0]["cpu_usage"] == cpu_usage
    assert metrics.iloc[0]["memory_usage"] == memory_usage
    assert metrics.iloc[0]["active_agents"] == active_agents
    assert metrics.iloc[0]["total_requests"] == total_requests


def test_get_agent_logs_with_date_range(pipeline):
    now = datetime.now()
    agent_id = "test_agent"
    pipeline.log_agent_action(
        agent_id=agent_id,
        action="old_action",
        input_data={},
        output_data={},
        status="success",
    )
    pipeline.log_agent_action(
        agent_id=agent_id,
        action="new_action",
        input_data={},
        output_data={},
        status="success",
    )
