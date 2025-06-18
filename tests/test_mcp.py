"""
MCP (Model Control Plane) 테스트
"""

from unittest.mock import Mock, patch

import pytest

from palantir.services.mcp.test_mcp import TestMCP


@pytest.mark.unit
@pytest.mark.mcp
class TestTestMCP:
    """TestMCP 클래스 테스트"""

    @pytest.fixture
    def test_mcp(self):
        """테스트용 TestMCP 인스턴스를 생성합니다."""
        return TestMCP()

    def test_init(self, test_mcp):
        """초기화 테스트"""
        assert test_mcp.test_dir == "tests"
        assert test_mcp.test_results == []

    def test_run_tests_all(self, test_mcp):
        """모든 테스트 실행 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="테스트 통과",
                stderr=""
            )
            
            results = test_mcp.run_tests()
            
            assert len(results) == 5  # pytest, flake8, mypy, bandit, radon
            assert all(result["success"] for result in results)
            assert mock_run.call_count == 5

    def test_run_tests_specific(self, test_mcp):
        """특정 테스트 실행 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="테스트 통과",
                stderr=""
            )
            
            results = test_mcp.run_tests(["pytest", "flake8"])
            
            assert len(results) == 2
            assert all(result["success"] for result in results)
            assert mock_run.call_count == 2

    def test_run_tests_failure(self, test_mcp):
        """테스트 실패 케이스 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="테스트 실패",
                stderr="오류 발생"
            )
            
            results = test_mcp.run_tests(["pytest"])
            
            assert len(results) == 1
            assert not results[0]["success"]
            assert results[0]["stderr"] == "오류 발생"

    def test_get_last_results(self, test_mcp):
        """최근 테스트 결과 조회 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="테스트 통과",
                stderr=""
            )
            
            test_mcp.run_tests(["pytest"])
            results = test_mcp.get_last_results()
            
            assert len(results) == 1
            assert results[0]["type"] == "pytest"
            assert results[0]["success"]
