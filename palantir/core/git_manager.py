"""Git 워크플로우 관리 시스템"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from git import Repo, GitCommandError
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CommitInfo(BaseModel):
    """커밋 정보"""
    hash: str = Field(description="커밋 해시")
    message: str = Field(description="커밋 메시지")
    author: str = Field(description="작성자")
    date: datetime = Field(description="작성일")
    files: List[str] = Field(description="변경된 파일 목록")


class BranchInfo(BaseModel):
    """브랜치 정보"""
    name: str = Field(description="브랜치 이름")
    current: bool = Field(description="현재 브랜치 여부")
    remote: Optional[str] = Field(default=None, description="원격 브랜치")
    commits: List[CommitInfo] = Field(default_factory=list, description="커밋 목록")


class GitManager:
    """Git 워크플로우 관리 시스템"""

    def __init__(self, repo_path: str = "."):
        """
        Args:
            repo_path: Git 저장소 경로
        """
        self.repo = Repo(repo_path)
        self.repo_path = Path(repo_path)
        self.allowed_commands = {
            "add", "commit", "push", "pull", "checkout", "branch",
            "merge", "rebase", "fetch", "status"
        }

        # 기본 브랜치를 main으로 설정
        if "master" in self.repo.heads:
            self.repo.heads["master"].rename("main")

    def _validate_branch_name(self, name: str) -> bool:
        """브랜치 이름 유효성 검사

        Args:
            name: 브랜치 이름

        Returns:
            bool: 유효성 여부
        """
        # Git 브랜치 이름 규칙:
        # - ASCII 문자로 시작
        # - 특수문자는 - _ / . 만 허용
        # - 연속된 점(..) 불가
        # - 끝에 점(.) 불가
        # - 어떤 위치에도 공백 불가
        # - ~, ^, :, ?, *, [ 등 Git 예약어 불가
        # - 점(.)으로 시작 불가
        # - 점(.)으로 끝나지 않아야 함
        # - 연속된 점(..)이 없어야 함
        # - 슬래시(/) 뒤에 점(.)이 없어야 함
        if not name or ".." in name or name.startswith(".") or name.endswith("."):
            return False
        if "/" in name and any(part.startswith(".") for part in name.split("/")):
            return False
        pattern = r"^[A-Za-z0-9][A-Za-z0-9-_/\.]*[A-Za-z0-9]$"
        return bool(re.match(pattern, name))

    def _validate_commit_message(self, message: str) -> bool:
        """커밋 메시지 유효성 검사

        Args:
            message: 커밋 메시지

        Returns:
            bool: 유효성 여부
        """
        # 커밋 메시지 규칙:
        # - 첫 줄은 50자 이내
        # - 두 번째 줄은 비워두기
        # - 본문은 72자 이내로 줄바꿈
        # - 빈 메시지 불가
        lines = message.split("\n")
        if not lines or not lines[0]:
            return False
        if len(lines[0]) > 50:
            return False
        if len(lines) > 1 and lines[1]:
            return False
        if any(len(line) > 72 for line in lines[2:]):
            return False
        return True

    def _format_commit_message(self, message: str, type: str = "feat") -> str:
        """커밋 메시지 포맷팅

        Args:
            message: 커밋 메시지
            type: 커밋 타입 (feat/fix/docs/style/refactor/test/chore)

        Returns:
            str: 포맷팅된 커밋 메시지
        """
        # 커밋 메시지 포맷:
        # type(scope): subject
        #
        # body
        #
        # footer
        lines = message.split("\n")
        subject = lines[0]
        body = "\n".join(lines[1:]) if len(lines) > 1 else ""

        if not subject.startswith(f"{type}:"):
            subject = f"{type}: {subject}"

        if body:
            body = body.strip()
            return f"{subject}\n\n{body}"
        return subject

    async def create_branch(self, name: str, base: Optional[str] = None) -> bool:
        """새 브랜치 생성

        Args:
            name: 브랜치 이름
            base: 기준 브랜치 (기본값: 현재 브랜치)

        Returns:
            bool: 성공 여부
        """
        try:
            if not self._validate_branch_name(name):
                raise ValueError(f"유효하지 않은 브랜치 이름: {name}")

            if base:
                base_branch = self.repo.heads[base]
                base_branch.checkout()
            
            self.repo.create_head(name)
            self.repo.heads[name].checkout()
            logger.info(f"브랜치 생성 성공: {name}")
            return True
        except Exception as e:
            logger.error(f"브랜치 생성 실패: {str(e)}")
            return False

    async def commit_changes(
        self,
        message: str,
        type: str = "feat",
        files: Optional[List[str]] = None
    ) -> bool:
        """변경사항 커밋

        Args:
            message: 커밋 메시지
            type: 커밋 타입
            files: 커밋할 파일 목록 (기본값: 모든 변경사항)

        Returns:
            bool: 성공 여부
        """
        try:
            formatted_message = self._format_commit_message(message, type)
            if not self._validate_commit_message(formatted_message):
                raise ValueError(f"유효하지 않은 커밋 메시지: {formatted_message}")

            if files:
                self.repo.index.add(files)
            else:
                self.repo.index.add("*")

            self.repo.index.commit(formatted_message)
            logger.info(f"커밋 성공: {formatted_message}")
            return True
        except Exception as e:
            logger.error(f"커밋 실패: {str(e)}")
            return False

    async def push_changes(
        self,
        branch: Optional[str] = None,
        remote: str = "origin"
    ) -> bool:
        """변경사항 푸시

        Args:
            branch: 푸시할 브랜치 (기본값: 현재 브랜치)
            remote: 원격 저장소 (기본값: origin)

        Returns:
            bool: 성공 여부
        """
        try:
            if not self.repo.remotes:
                raise GitCommandError("push", "원격 저장소가 없습니다.")

            if branch:
                ref = f"refs/heads/{branch}:refs/heads/{branch}"
            else:
                ref = f"refs/heads/{self.repo.active_branch.name}"

            self.repo.remote(remote).push(ref)
            logger.info(f"푸시 성공: {ref}")
            return True
        except Exception as e:
            logger.error(f"푸시 실패: {str(e)}")
            return False

    async def get_branch_info(self, name: Optional[str] = None) -> BranchInfo:
        """브랜치 정보 조회

        Args:
            name: 브랜치 이름 (기본값: 현재 브랜치)

        Returns:
            BranchInfo: 브랜치 정보
        """
        try:
            if name:
                branch = self.repo.heads[name]
            else:
                branch = self.repo.active_branch

            commits = []
            for commit in self.repo.iter_commits(branch.name):
                commits.append(CommitInfo(
                    hash=commit.hexsha,
                    message=commit.message,
                    author=commit.author.name,
                    date=datetime.fromtimestamp(commit.authored_date),
                    files=[diff.a_path for diff in commit.diff()]
                ))

            return BranchInfo(
                name=branch.name,
                current=branch.name == self.repo.active_branch.name,
                remote=branch.tracking_branch().name if branch.tracking_branch() else None,
                commits=commits
            )
        except Exception as e:
            logger.error(f"브랜치 정보 조회 실패: {str(e)}")
            return BranchInfo(name="", current=False, remote=None)

    async def get_status(self) -> Dict[str, Any]:
        """저장소 상태 조회

        Returns:
            Dict[str, Any]: 상태 정보
        """
        try:
            status = self.repo.git.status(porcelain=True)
            untracked = []
            modified = []
            deleted = []

            for line in status.split("\n"):
                if not line:
                    continue
                state = line[:2]
                path = line[3:]
                if state == "??":
                    untracked.append(path)
                elif state == " M" or state == "M ":
                    modified.append(path)
                elif state == " D" or state == "D ":
                    deleted.append(path)

            return {
                "branch": self.repo.active_branch.name,
                "untracked": untracked,
                "modified": modified,
                "deleted": deleted,
                "is_dirty": bool(untracked or modified or deleted),
                "remotes": [remote.name for remote in self.repo.remotes]
            }
        except Exception as e:
            logger.error(f"상태 조회 실패: {str(e)}")
            return {
                "error": str(e)
            } 