import os
import platform
import sys


class NotWSLError(EnvironmentError):
    pass


def is_wsl() -> bool:
    if os.environ.get("IGNORE_WSL_CHECK") == "1":
        return True
    if os.name != "posix":
        return False
    try:
        with open("/proc/version", "r", encoding="utf-8", errors="ignore") as fp:
            version = fp.read().lower()
            if "microsoft" in version or "wsl" in version:
                return True
    except FileNotFoundError:
        pass
    release = platform.release().lower()
    return "microsoft" in release or "wsl" in release


def is_linux() -> bool:
    return os.name == "posix" and platform.system().lower() == "linux"


def main() -> None:
    if not (is_wsl() or is_linux()):
        raise NotWSLError("Linux/WSL 환경이 필요합니다")
    if sys.version_info < (3, 11):
        sys.stderr.write("Python 3.11 이상이 필요합니다\n")
        sys.exit(1)
    print("Linux environment check passed")


if __name__ == "__main__":
    main()
