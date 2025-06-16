import subprocess
from typing import Optional

from ...core.exceptions import MCPError


class GitMCP:
    """Wrapper around git commands."""

    def __init__(self, repo_dir: Optional[str] = None):
        self.repo_dir = repo_dir or "."
        self.allowed_cmds = {"add", "commit", "push", "checkout"}

    def run_git(self, *args) -> str:
        if args[0] not in self.allowed_cmds:
            raise MCPError(f"허용되지 않은 git 명령: {args[0]}")
        result = subprocess.run(
            ["git", *args], cwd=self.repo_dir, capture_output=True, text=True
        )
        if result.returncode != 0:
            raise MCPError(result.stderr.strip())
        return result.stdout

    async def commit(self, message: str) -> None:
        self.run_git("add", ".")
        self.run_git("commit", "-m", message)

    async def push(self, branch: Optional[str] = None) -> None:
        args = ["push"]
        if branch:
            args.extend(["origin", branch])
        self.run_git(*args)
