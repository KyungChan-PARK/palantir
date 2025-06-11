import os
import platform


class NotWSLError(EnvironmentError):
    """Raised when the application is NOT running inside a Linux environment."""


_DEF_MSG = (
    "이 애플리케이션은 Linux 또는 WSL(Windows Subsystem for Linux) 환경에서 실행되어야 합니다.\n"
    "PowerShell 또는 Windows 네이티브 터미널이 아닌, Linux 쉘에서 재실행해 주세요."
)


def is_wsl() -> bool:
    """WSL 환경 여부를 반환한다.

    방법:
    1. /proc/version 문자열에 'microsoft' 포함 여부 검사
    2. platform.release() 에서 'microsoft' / 'WSL' 키워드 검색
    """
    if os.environ.get("IGNORE_WSL_CHECK") == "1":
        return True
    if os.name != "posix":
        # Windows 파워쉘 등
        return False

    try:
        with open("/proc/version", "r", encoding="utf-8", errors="ignore") as fp:
            version = fp.read().lower()
            if "microsoft" in version or "wsl" in version:
                return True
    except FileNotFoundError:
        pass

    # Fallback: platform.release()
    release = platform.release().lower()
    return "microsoft" in release or "wsl" in release


def is_linux() -> bool:
    """Return True if running on a generic Linux system."""
    return os.name == "posix" and platform.system().lower() == "linux"


def assert_wsl(msg: str | None = None) -> None:
    """Linux/WSL 환경이 아니면 예외를 던진다."""
    if not (is_wsl() or is_linux()):
        raise NotWSLError(msg or _DEF_MSG)
