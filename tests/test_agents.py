import pytest
from unittest.mock import patch

from palantir.core.agent_impls import PlannerAgent, DeveloperAgent, ReviewerAgent


def test_planner_process():
    planner = PlannerAgent("planner")
    with patch("palantir.services.mcp.llm_mcp.LLMMCP.generate") as mock_gen:
        mock_gen.return_value = "['a', 'b']"
        tasks = planner.process("do something")
        assert tasks == ["a", "b"]
        mock_gen.assert_called_once()


def test_developer_process():
    developer = DeveloperAgent("dev")
    with patch("palantir.services.mcp.llm_mcp.LLMMCP.generate") as mock_gen, \
        patch.object(developer.file, "write_file"), \
        patch.object(developer.git, "commit"):
        mock_gen.return_value = "print('hi')"
        results = developer.process(["task"], state=None)
        assert results[0]["task"] == "task"
        assert results[0]["file"].endswith(".py")
        mock_gen.assert_called_once()


def test_reviewer_process():
    reviewer = ReviewerAgent("rev")
    with patch("palantir.services.mcp.llm_mcp.LLMMCP.generate") as mock_gen, \
        patch.object(reviewer.test, "run_tests", return_value="ok"):
        mock_gen.return_value = "looks good"
        results = reviewer.process([{"task": "t", "file": "f", "code": "code"}])
        assert results[0]["feedback"] == "looks good"
        mock_gen.assert_called_once()
