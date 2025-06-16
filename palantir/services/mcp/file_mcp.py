import os
from typing import Optional


class FileMCP:
    """파일 시스템 접근을 안전하게 추상화하는 MCP 계층"""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = os.path.abspath(base_dir or os.getcwd())

    def _safe_path(self, path: str) -> str:
        abs_path = os.path.abspath(os.path.join(self.base_dir, path))
        if not abs_path.startswith(self.base_dir):
            raise PermissionError(f"허용되지 않은 경로 접근: {abs_path}")
        return abs_path

    def read_file(self, path: str) -> str:
        try:
            abs_path = self._safe_path(path)
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"[FileMCP] 파일 읽기: {abs_path}")
            return content
        except Exception as e:
            print(f"[FileMCP 오류] 파일 읽기 실패: {e}")
            return f"[FileMCP 오류] {e}"

    def write_file(self, path: str, content: str) -> None:
        try:
            abs_path = self._safe_path(path)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[FileMCP] 파일 쓰기: {abs_path}")
        except Exception as e:
            print(f"[FileMCP 오류] 파일 쓰기 실패: {e}")

    def list_files(self, subdir: Optional[str] = None):
        try:
            target_dir = self._safe_path(subdir) if subdir else self.base_dir
            files = os.listdir(target_dir)
            print(f"[FileMCP] 파일 목록: {target_dir}")
            return files
        except Exception as e:
            print(f"[FileMCP 오류] 파일 목록 실패: {e}")
            return []
