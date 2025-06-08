import os
import shutil
import subprocess
import sys
from typing import Tuple

from palantir.utils.wsl import assert_wsl, is_wsl

REQUIRED_COMMANDS = [
    ("python", "Python 3.13 이상 (python 또는 python3)"),
    ("node", "Node.js 18.x 이상"),
    ("yarn", "Yarn 패키지 매니저"),
    ("docker", "Docker 엔진 / Docker Compose"),
]

# python3 명령 존재 시 python 없을 수도 있으므로 동적으로 치환
if shutil.which("python") is None and shutil.which("python3") is not None:
    REQUIRED_COMMANDS = [
        ("python3", "Python 3.13 이상"),
        *REQUIRED_COMMANDS[1:],
    ]

REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
]


class CheckFailed(Exception):
    pass


def _run(cmd: list[str] | str) -> Tuple[str, int]:
    """명령 실행 후 (stdout, returncode)를 반환"""
    try:
        proc = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.stdout.strip() + proc.stderr.strip(), proc.returncode
    except FileNotFoundError:
        return "", 1


def check_commands() -> None:
    missing = []
    for cmd, desc in REQUIRED_COMMANDS:
        if shutil.which(cmd) is None:
            missing.append(f"{cmd} ({desc}) 미설치")
            continue
        # 버전 체크 (python/node)
        if cmd in ("python", "python3"):
            out, _ = _run([cmd, "-c", "import sys, json; print(sys.version_info[:3])"])
            try:
                major, minor, patch = eval(out)
                if major < 3 or (major == 3 and minor < 13):
                    missing.append("Python 3.13 이상 필요")
            except Exception:
                missing.append("Python 버전 파싱 실패")
        elif cmd == "node":
            out, _ = _run(["node", "--version"])
            ver = out.lstrip("v").split(".")
            try:
                major = int(ver[0])
                if major < 18:
                    missing.append("Node.js 18.x 이상 필요")
            except Exception:
                missing.append("Node.js 버전 파싱 실패")
    if missing:
        raise CheckFailed("\n".join(missing))


def check_env_vars() -> None:
    missing_envs = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_envs:
        raise CheckFailed(f"필수 환경변수 누락: {', '.join(missing_envs)}")


def main() -> None:
    try:
        if not is_wsl():
            raise CheckFailed("WSL 환경이 아님. Ubuntu WSL2 등에서 실행해 주세요.")
        assert_wsl()
        check_commands()
        check_env_vars()
        print("[WSL-ENV] ✅ 모든 필수 의존성이 충족되었습니다.")
        sys.exit(0)
    except CheckFailed as e:
        print(f"[WSL-ENV] ❌ 환경 검사 실패:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 