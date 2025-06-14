import subprocess
import json
from typing import Optional
from palantir.core.backup import notify_slack

class TestMCP:
    """테스트 실행을 안전하게 추상화하는 MCP 계층"""
    def __init__(self, test_dir: Optional[str] = None):
        self.test_dir = test_dir or "tests"

    def run_tests(self):
        # 기존 pytest 실행
        result = subprocess.run(["pytest", "-q", "--disable-warnings", "--maxfail=1", "--tb=short", "--json-report"], capture_output=True, text=True)
        return {"type": "pytest", "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}

    def run_flake8(self):
        result = subprocess.run(["flake8", ".", "--format=json"], capture_output=True, text=True)
        try:
            output = json.loads(result.stdout)
        except Exception:
            output = result.stdout
        return {"type": "flake8", "returncode": result.returncode, "output": output}

    def run_mypy(self):
        result = subprocess.run(["mypy", ".", "--ignore-missing-imports", "--show-error-codes", "--no-color-output"], capture_output=True, text=True)
        return {"type": "mypy", "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}

    def run_bandit(self):
        result = subprocess.run(["bandit", "-r", ".", "-f", "json"], capture_output=True, text=True)
        try:
            output = json.loads(result.stdout)
        except Exception:
            output = result.stdout
        return {"type": "bandit", "returncode": result.returncode, "output": output}

    def run_radon(self):
        result = subprocess.run(["radon", "cc", ".", "-j"], capture_output=True, text=True)
        try:
            output = json.loads(result.stdout)
        except Exception:
            output = result.stdout
        return {"type": "radon", "returncode": result.returncode, "output": output}

    def run_all_checks(self):
        results = []
        results.append(self.run_tests())
        results.append(self.run_flake8())
        results.append(self.run_mypy())
        results.append(self.run_bandit())
        results.append(self.run_radon())
        return results

    def run_tests(self) -> str:
        results = []
        alerts = []
        # 1. pytest
        pytest_result = subprocess.run(["pytest", self.test_dir, "-v"], capture_output=True, text=True)
        if pytest_result.returncode != 0:
            results.append(f"[테스트 실패] pytest\n{pytest_result.stdout}\n{pytest_result.stderr}")
            alerts.append("pytest")
        else:
            results.append(f"[테스트 통과] pytest\n{pytest_result.stdout}")
        # 2. flake8
        flake8_result = subprocess.run(["flake8", "palantir/"], capture_output=True, text=True)
        if flake8_result.returncode != 0:
            results.append(f"[린트 실패] flake8\n{flake8_result.stdout}\n{flake8_result.stderr}")
            alerts.append("flake8")
        else:
            results.append(f"[린트 통과] flake8\n{flake8_result.stdout}")
        # 3. mypy
        mypy_result = subprocess.run(["mypy", "palantir/"], capture_output=True, text=True)
        if mypy_result.returncode != 0:
            results.append(f"[정적분석 실패] mypy\n{mypy_result.stdout}\n{mypy_result.stderr}")
            alerts.append("mypy")
        else:
            results.append(f"[정적분석 통과] mypy\n{mypy_result.stdout}")
        # 4. bandit(보안)
        try:
            bandit_result = subprocess.run(["bandit", "-r", "palantir/", "-f", "json"], capture_output=True, text=True)
            if bandit_result.returncode != 0 or '"HIGH"' in bandit_result.stdout:
                results.append(f"[보안 취약점] bandit\n{bandit_result.stdout}\n{bandit_result.stderr}")
                alerts.append("bandit")
            else:
                results.append(f"[보안 통과] bandit\n{bandit_result.stdout}")
        except Exception as e:
            results.append(f"[bandit 실행 오류] {str(e)}")
            alerts.append("bandit-error")
        # 5. radon(복잡도)
        try:
            radon_result = subprocess.run(["radon", "cc", "-n", "C", "palantir/"], capture_output=True, text=True)
            if "F" in radon_result.stdout or "E" in radon_result.stdout:
                results.append(f"[복잡도 경고] radon\n{radon_result.stdout}")
                alerts.append("radon")
            else:
                results.append(f"[복잡도 통과] radon\n{radon_result.stdout}")
        except Exception as e:
            results.append(f"[radon 실행 오류] {str(e)}")
            alerts.append("radon-error")
        # 6. safety(취약점)
        try:
            safety_result = subprocess.run(["safety", "check"], capture_output=True, text=True)
            if safety_result.returncode != 0:
                results.append(f"[취약점 발견] safety\n{safety_result.stdout}\n{safety_result.stderr}")
                alerts.append("safety")
            else:
                results.append(f"[취약점 없음] safety\n{safety_result.stdout}")
        except Exception as e:
            results.append(f"[safety 실행 오류] {str(e)}")
            alerts.append("safety-error")
        # 7. mutmut(뮤테이션)
        try:
            mutmut_result = subprocess.run(["mutmut", "run", "--paths-to-mutate", "palantir/"], capture_output=True, text=True)
            if mutmut_result.returncode != 0:
                results.append(f"[뮤테이션 테스트 실패] mutmut\n{mutmut_result.stdout}\n{mutmut_result.stderr}")
                alerts.append("mutmut")
            else:
                results.append(f"[뮤테이션 테스트 통과] mutmut\n{mutmut_result.stdout}")
        except Exception as e:
            results.append(f"[mutmut 실행 오류] {str(e)}")
            alerts.append("mutmut-error")
        # 정책/가드레일/알림
        if alerts:
            notify_slack(f"[PalantirAIP][테스트/정책 경고] 자동화 테스트/정책 위반 감지: {alerts}\n요약: {results[-1] if results else ''}")
        return "\n\n".join(results) 