import os
from typing import Optional

from ...core.exceptions import MCPError


class FileMCP:
    """Filesystem access abstraction."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = os.path.abspath(base_dir or os.getcwd())

    def _safe_path(self, path: str) -> str:
        abs_path = os.path.abspath(os.path.join(self.base_dir, str(path)))
        if not abs_path.startswith(self.base_dir):
            raise MCPError(f"허용되지 않은 경로 접근: {abs_path}")
        return abs_path

    def validate_file(self, filename: str, max_size: int) -> bool:
        if not filename.split(".")[-1] in {"py", "txt", "md"}:
            raise MCPError("잘못된 확장자")
        if max_size and os.path.exists(filename) and os.path.getsize(filename) > max_size:
            raise MCPError("파일 크기 초과")
        return True

    async def read_file(self, path: str) -> str:
        try:
            abs_path = self._safe_path(path)
            with open(abs_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise MCPError(str(e)) from e

    async def write_file(self, path: str, content: str) -> None:
        try:
            abs_path = self._safe_path(path)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            raise MCPError(str(e)) from e
