import importlib.util
import pathlib
import sys
import types
from unittest.mock import patch

sys.modules.setdefault("git", types.ModuleType("git"))
sys.modules.setdefault("fastapi", types.ModuleType("fastapi"))
sys.modules.setdefault("pandas", types.ModuleType("pandas"))
sys.modules.setdefault("requests", types.ModuleType("requests"))
sys.modules.setdefault("weaviate", types.ModuleType("weaviate"))
pydantic_stub = types.ModuleType("pydantic")
pydantic_stub.BaseModel = type("BaseModel", (), {})
pydantic_stub.Field = lambda *_, **__: None
sys.modules.setdefault("pydantic", pydantic_stub)
core_path = pathlib.Path(__file__).resolve().parents[2] / "palantir" / "core"
core_stub = types.ModuleType("palantir.core")
core_stub.__path__ = [str(core_path)]
sys.modules.setdefault("palantir.core", core_stub)

ORCH_PATH = core_path / "orchestrator.py"
spec = importlib.util.spec_from_file_location("orchestrator", ORCH_PATH)
orch_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orch_module)
Orchestrator = orch_module.Orchestrator


def _mock_dev(task_list, state=None):
    return [{"task": t, "file": f"{t}.py", "code": "print('x')"} for t in task_list]


def _mock_review(dev_results, state=None):
    return [
        {
            "task": d["task"],
            "file": d["file"],
            "test_result": "테스트 통과",
            "feedback": "ok",
        }
        for d in dev_results
    ]


def _mock_review_fail(dev_results, state=None):
    return [
        {
            "task": d["task"],
            "file": d["file"],
            "test_result": "테스트 실패",
            "feedback": "bad",
        }
        for d in dev_results
    ]


def _mock_improve(review_results, state=None):
    return {"improvements": []}


@patch("palantir.core.backup.notify_slack")
@patch("palantir.services.mcp.test_mcp.TestMCP.run_all_checks", return_value=[])
@patch(
    "palantir.core.agent_impls.SelfImprovementAgent.process", side_effect=_mock_improve
)
@patch("palantir.core.agent_impls.ReviewerAgent.process", side_effect=_mock_review)
@patch("palantir.core.agent_impls.DeveloperAgent.process", side_effect=_mock_dev)
@patch("palantir.core.agent_impls.PlannerAgent.process", return_value=["t1", "t2"])
def test_orchestrator_loop_ok(*_):
    orch = Orchestrator(execution_mode="parallel")
    results = orch.run("t1. t2")
    assert len(results) == 2
    assert all(not r.alert_sent for r in results)


@patch("palantir.core.backup.notify_slack")
@patch("palantir.services.mcp.test_mcp.TestMCP.run_all_checks", return_value=[])
@patch(
    "palantir.core.agent_impls.SelfImprovementAgent.process", side_effect=_mock_improve
)
@patch("palantir.core.agent_impls.ReviewerAgent.process", side_effect=_mock_review_fail)
@patch("palantir.core.agent_impls.DeveloperAgent.process", side_effect=_mock_dev)
@patch("palantir.core.agent_impls.PlannerAgent.process", return_value=["t1"])
def test_orchestrator_policy_block(*_):
    orch = Orchestrator()
    results = orch.run("t1")
    assert len(results) == 1
    assert results[0].alert_sent
