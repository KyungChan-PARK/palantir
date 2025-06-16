import subprocess
from typing import Optional


class GitMCP:
    """Git 명령을 안전하게 추상화하는 MCP 계층"""

    def __init__(self, repo_dir: Optional[str] = None):
        self.repo_dir = repo_dir or "."
        self.allowed_cmds = {"add", "commit", "push", "checkout"}

    def run_git(self, *args) -> str:
        if args[0] not in self.allowed_cmds:
            raise PermissionError(f"허용되지 않은 git 명령: {args[0]}")
        try:
            result = subprocess.run(
                ["git"] + list(args), cwd=self.repo_dir, capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"[GitMCP 오류] git {' '.join(args)} 실패: {result.stderr}")
                raise Exception(f"git {' '.join(args)} 실패: {result.stderr}")
            print(f"[GitMCP] git {' '.join(args)} 성공")
            return result.stdout
        except Exception as e:
            print(f"[GitMCP 예외] {e}")
            return f"[GitMCP 오류] {e}"

    def commit(self, message: str):
        self.run_git("add", ".")
        self.run_git("commit", "-m", message)

    def push(self, branch: Optional[str] = None):
        args = ["push"]
        if branch:
            args.append("origin")
            args.append(branch)
        self.run_git(*args)

    def create_branch(self, branch: str):
        self.run_git("checkout", "-b", branch)
