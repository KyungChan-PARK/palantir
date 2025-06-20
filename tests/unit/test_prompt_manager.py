"""프롬프트 관리 시스템 단위 테스트"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from palantir.core.prompt_manager import PromptManager, PromptTemplate
from palantir.core.llm_manager import LLMManager
from palantir.core.shared_memory import SharedMemory
from palantir.core.context_manager import ContextManager


@pytest.fixture
def llm_manager():
    """LLM 매니저 목업"""
    manager = AsyncMock(spec=LLMManager)
    manager.generate = AsyncMock(return_value="LLM 응답")
    return manager


@pytest.fixture
def shared_memory():
    """공유 메모리 목업"""
    memory = AsyncMock(spec=SharedMemory)
    memory.store = AsyncMock(return_value=True)
    memory.get = AsyncMock(return_value=None)
    memory.delete = AsyncMock(return_value=True)
    memory.search = AsyncMock(return_value=[])
    return memory


@pytest.fixture
def context_manager():
    """컨텍스트 매니저 목업"""
    manager = AsyncMock(spec=ContextManager)
    manager.get_system_context = AsyncMock(return_value="시스템 컨텍스트")
    return manager


@pytest.fixture
def prompt_manager(llm_manager, shared_memory, context_manager):
    """프롬프트 매니저 인스턴스"""
    return PromptManager(llm_manager, shared_memory, context_manager)


@pytest.fixture
def sample_template():
    """샘플 프롬프트 템플릿"""
    return PromptTemplate(
        name="test_template",
        description="테스트용 템플릿",
        system_message="시스템 메시지",
        template="테스트 프롬프트 {param1} {param2}",
        parameters=["param1", "param2"],
        tags=["test"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class TestPromptManager:
    """프롬프트 매니저 테스트 스위트"""

    @pytest.mark.asyncio
    async def test_create_template(self, prompt_manager, sample_template):
        """템플릿 생성 테스트"""
        result = await prompt_manager.create_template(sample_template)
        assert result is True
        prompt_manager.shared_memory.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_template(self, prompt_manager, sample_template):
        """템플릿 조회 테스트"""
        # 템플릿이 없는 경우
        template = await prompt_manager.get_template("non_existent")
        assert template is None

        # 템플릿이 있는 경우
        prompt_manager.shared_memory.get.return_value = sample_template.dict()
        template = await prompt_manager.get_template(sample_template.name)
        assert template is not None
        assert template.name == sample_template.name

    @pytest.mark.asyncio
    async def test_update_template(self, prompt_manager, sample_template):
        """템플릿 업데이트 테스트"""
        result = await prompt_manager.update_template(sample_template)
        assert result is True
        prompt_manager.shared_memory.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_template(self, prompt_manager):
        """템플릿 삭제 테스트"""
        result = await prompt_manager.delete_template("test_template")
        assert result is True
        prompt_manager.shared_memory.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_templates(self, prompt_manager, sample_template):
        """템플릿 검색 테스트"""
        # 검색 결과가 없는 경우
        templates = await prompt_manager.search_templates(["test"])
        assert len(templates) == 0

        # 검색 결과가 있는 경우
        prompt_manager.shared_memory.search.return_value = [sample_template.dict()]
        templates = await prompt_manager.search_templates(["test"])
        assert len(templates) == 1
        assert templates[0].name == sample_template.name

    @pytest.mark.asyncio
    async def test_generate_prompt(self, prompt_manager, sample_template):
        """프롬프트 생성 테스트"""
        prompt_manager.shared_memory.get.return_value = sample_template.dict()
        
        # 기본 프롬프트 생성
        prompt = await prompt_manager.generate_prompt(
            "test_template",
            {"param1": "값1", "param2": "값2"}
        )
        assert "시스템 컨텍스트" in prompt
        assert "값1" in prompt
        assert "값2" in prompt

        # 추가 컨텍스트가 있는 경우
        prompt = await prompt_manager.generate_prompt(
            "test_template",
            {"param1": "값1", "param2": "값2"},
            "추가 컨텍스트"
        )
        assert "시스템 컨텍스트" in prompt
        assert "추가 컨텍스트" in prompt
        assert "값1" in prompt
        assert "값2" in prompt

        # 템플릿이 없는 경우
        prompt_manager.shared_memory.get.return_value = None
        with pytest.raises(ValueError):
            await prompt_manager.generate_prompt(
                "non_existent",
                {"param1": "값1", "param2": "값2"}
            )

    @pytest.mark.asyncio
    async def test_execute_prompt(self, prompt_manager, sample_template):
        """프롬프트 실행 테스트"""
        prompt_manager.shared_memory.get.return_value = sample_template.dict()
        
        # 기본 실행
        response = await prompt_manager.execute_prompt(
            "test_template",
            {"param1": "값1", "param2": "값2"}
        )
        assert response == "LLM 응답"
        prompt_manager.llm.generate.assert_called_once()

        # 추가 설정이 있는 경우
        prompt_manager.llm.generate.reset_mock()
        response = await prompt_manager.execute_prompt(
            "test_template",
            {"param1": "값1", "param2": "값2"},
            additional_context="추가 컨텍스트",
            temperature=0.7
        )
        assert response == "LLM 응답"
        prompt_manager.llm.generate.assert_called_once()

        # 템플릿이 없는 경우
        prompt_manager.shared_memory.get.return_value = None
        with pytest.raises(ValueError):
            await prompt_manager.execute_prompt(
                "non_existent",
                {"param1": "값1", "param2": "값2"}
            ) 