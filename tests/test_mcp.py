"""
MCP (Model Control Plane) 테스트
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import json
import aiohttp
from palantir.services.mcp.base import BaseMCP
from palantir.services.mcp.llm import LLM_MCP
from palantir.services.mcp.file import File_MCP
from palantir.services.mcp.git import Git_MCP
from palantir.services.mcp.web import Web_MCP
from palantir.core.exceptions import MCPError

@pytest.mark.unit
@pytest.mark.mcp
class TestBaseMCP:
    """BaseMCP 클래스 테스트"""

    @pytest.fixture
    def mcp(self, mock_mcp_config):
        """테스트용 BaseMCP 인스턴스를 생성합니다."""
        return BaseMCP(config=mock_mcp_config)

    def test_init(self, mcp, mock_mcp_config):
        """초기화 테스트"""
        assert mcp.config == mock_mcp_config

    def test_validate_config(self, mock_mcp_config):
        """설정 유효성 검사 테스트"""
        # 유효한 설정
        BaseMCP.validate_config(mock_mcp_config)

        # 잘못된 설정
        invalid_config = {}
        with pytest.raises(ValueError):
            BaseMCP.validate_config(invalid_config)

@pytest.mark.unit
@pytest.mark.mcp
class TestLLM_MCP:
    """LLM_MCP 클래스 테스트"""

    @pytest.fixture
    def llm_mcp(self, mock_mcp_config):
        """테스트용 LLM_MCP 인스턴스를 생성합니다."""
        return LLM_MCP(config=mock_mcp_config["llm"])

    @pytest.mark.asyncio
    async def test_generate(self, llm_mcp, mock_llm_response):
        """LLM 생성 테스트"""
        with patch("openai.ChatCompletion.create") as mock_create:
            mock_create.return_value = mock_llm_response
            response = await llm_mcp.generate(
                prompt="테스트 프롬프트",
                model="gpt-4",
                temperature=0.7,
                max_tokens=1000
            )
            assert response == mock_llm_response

    @pytest.mark.asyncio
    async def test_generate_error(self, llm_mcp):
        """LLM 생성 에러 처리 테스트"""
        with patch("openai.ChatCompletion.create") as mock_create:
            mock_create.side_effect = Exception("API 오류")
            with pytest.raises(MCPError):
                await llm_mcp.generate(
                    prompt="테스트 프롬프트",
                    model="gpt-4"
                )

@pytest.mark.unit
@pytest.mark.mcp
class TestFile_MCP:
    """File_MCP 클래스 테스트"""

    @pytest.fixture
    def file_mcp(self, mock_mcp_config, temp_dir):
        """테스트용 File_MCP 인스턴스를 생성합니다."""
        config = mock_mcp_config["file"]
        config["base_path"] = str(temp_dir)
        return File_MCP(config=config)

    def test_validate_file(self, file_mcp):
        """파일 유효성 검사 테스트"""
        # 유효한 파일
        assert file_mcp.validate_file("test.py", 1000)

        # 잘못된 확장자
        with pytest.raises(MCPError):
            file_mcp.validate_file("test.exe", 1000)

        # 크기 초과
        with pytest.raises(MCPError):
            file_mcp.validate_file("test.py", 2000000)

    @pytest.mark.asyncio
    async def test_read_write_file(self, file_mcp, temp_dir):
        """파일 읽기/쓰기 테스트"""
        test_file = temp_dir / "test.py"
        test_content = "print('hello')"

        # 파일 쓰기
        await file_mcp.write_file(test_file, test_content)
        assert test_file.exists()

        # 파일 읽기
        content = await file_mcp.read_file(test_file)
        assert content == test_content

@pytest.mark.unit
@pytest.mark.mcp
class TestGit_MCP:
    """Git_MCP 클래스 테스트"""

    @pytest.fixture
    def git_mcp(self, mock_mcp_config, temp_dir):
        """테스트용 Git_MCP 인스턴스를 생성합니다."""
        config = mock_mcp_config["git"]
        config["repo_path"] = str(temp_dir)
        return Git_MCP(config=config)

    @pytest.mark.asyncio
    async def test_git_operations(self, git_mcp):
        """Git 작업 테스트"""
        with patch("git.Repo") as mock_repo:
            # 커밋
            await git_mcp.commit("테스트 커밋")
            mock_repo.return_value.index.commit.assert_called_once_with(
                "테스트 커밋"
            )

            # 푸시
            await git_mcp.push()
            mock_repo.return_value.remote.return_value.push.assert_called_once()

@pytest.mark.unit
@pytest.mark.mcp
class TestWeb_MCP:
    """Web_MCP 클래스 테스트"""

    @pytest.fixture
    def web_mcp(self, mock_mcp_config):
        """테스트용 Web_MCP 인스턴스를 생성합니다."""
        return Web_MCP(config=mock_mcp_config["web"])

    @pytest.mark.asyncio
    async def test_request(self, web_mcp):
        """웹 요청 테스트"""
        test_url = "http://test.com"
        test_response = {"status": "ok"}

        async with aiohttp.ClientSession() as session:
            with patch.object(session, "get") as mock_get:
                mock_response = Mock()
                mock_response.status = 200
                mock_response.json.return_value = test_response
                mock_get.return_value.__aenter__.return_value = mock_response

                response = await web_mcp.request(test_url)
                assert response == test_response

    @pytest.mark.asyncio
    async def test_request_error(self, web_mcp):
        """웹 요청 에러 처리 테스트"""
        test_url = "http://test.com"

        async with aiohttp.ClientSession() as session:
            with patch.object(session, "get") as mock_get:
                mock_get.side_effect = aiohttp.ClientError()
                
                with pytest.raises(MCPError):
                    await web_mcp.request(test_url) 