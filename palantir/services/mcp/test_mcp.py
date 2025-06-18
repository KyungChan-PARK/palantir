import json
import subprocess
from typing import Dict, List, Optional, Union

from palantir.core.backup import notify_slack


class TestMCP:
    """테스트 실행을 안전하게 추상화하는 MCP 계층"""

    def __init__(self, test_dir: Optional[str] = None):
        self.test_dir = test_dir or "tests"
        self.test_results: List[Dict[str, Union[str, int, dict]]] = []

    def _run_command(self, cmd: List[str], test_type: str) -> Dict[str, Union[str, int, dict]]:
        """테스트 명령어를 실행하고 결과를 표준화된 형식으로 반환"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = None
            
            # JSON 출력 파싱 시도
            if test_type in ["flake8", "bandit", "radon"]:
                try:
                    output = json.loads(result.stdout)
                except json.JSONDecodeError:
                    output = result.stdout

            return {
                "type": test_type,
                "returncode": result.returncode,
                "stdout": result.stdout if output is None else None,
                "stderr": result.stderr,
                "output": output,
                "success": result.returncode == 0
            }
        except Exception as e:
            return {
                "type": test_type,
                "returncode": -1,
                "stdout": None,
                "stderr": str(e),
                "output": None,
                "success": False
            }

    def run_tests(self, test_types: Optional[List[str]] = None) -> List[Dict[str, Union[str, int, dict]]]:
        """지정된 유형의 테스트들을 실행
        
        Args:
            test_types: 실행할 테스트 유형 목록. None이면 모든 테스트 실행
        """
        if test_types is None:
            test_types = ["pytest", "flake8", "mypy", "bandit", "radon"]

        self.test_results = []
        alerts = []

        test_commands = {
            "pytest": ["pytest", self.test_dir, "-v", "--disable-warnings", "--maxfail=1", "--tb=short", "--json-report"],
            "flake8": ["flake8", ".", "--format=json"],
            "mypy": ["mypy", ".", "--ignore-missing-imports", "--show-error-codes", "--no-color-output"],
            "bandit": ["bandit", "-r", ".", "-f", "json"],
            "radon": ["radon", "cc", ".", "-j"]
        }

        for test_type in test_types:
            if test_type not in test_commands:
                print(f"[경고] 알 수 없는 테스트 유형: {test_type}")
                continue

            result = self._run_command(test_commands[test_type], test_type)
            self.test_results.append(result)
            
            if not result["success"]:
                alerts.append(test_type)

        # 정책/가드레일/알림
        if alerts:
            notify_slack(
                f"[PalantirAIP][테스트/정책 경고] 자동화 테스트/정책 위반 감지: {alerts}\n"
                f"요약: {self.test_results[-1] if self.test_results else ''}"
            )

        return self.test_results

    def get_last_results(self) -> List[Dict[str, Union[str, int, dict]]]:
        """가장 최근 테스트 실행 결과 반환"""
        return self.test_results
