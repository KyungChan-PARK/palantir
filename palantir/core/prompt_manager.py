"""프롬프트 관리 시스템"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field

from .llm_manager import LLMManager
from .shared_memory import SharedMemory
from .context_manager import ContextManager

logger = logging.getLogger(__name__)


class PromptTemplate(BaseModel):
    """프롬프트 템플릿 모델"""
    name: str = Field(description="템플릿 이름")
    description: str = Field(description="템플릿 설명")
    system_message: str = Field(description="시스템 메시지")
    template: str = Field(description="프롬프트 템플릿")
    parameters: List[str] = Field(description="필요한 파라미터 목록")
    tags: List[str] = Field(default_factory=list, description="템플릿 태그")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class PromptManager:
    """프롬프트 관리 시스템"""

    def __init__(
        self,
        llm_manager: LLMManager,
        shared_memory: SharedMemory,
        context_manager: ContextManager
    ):
        """
        Args:
            llm_manager: LLM 매니저 인스턴스
            shared_memory: 공유 메모리 인스턴스
            context_manager: 컨텍스트 매니저 인스턴스
        """
        self.llm = llm_manager
        self.shared_memory = shared_memory
        self.context_manager = context_manager

        # 기본 프롬프트 템플릿 등록
        self._register_default_templates()

    async def _register_default_templates(self):
        """기본 프롬프트 템플릿 등록"""
        templates = [
            PromptTemplate(
                name="api_endpoint",
                description="새로운 API 엔드포인트 구현",
                system_message="""당신은 FastAPI 기반 백엔드 개발을 돕는 AI 어시스턴트입니다.
                프로젝트는 JWT 인증, PostgreSQL DB, 그리고 Pinecone 벡터 DB를 사용합니다.
                코드는 항상 타입 힌트를 포함하고, 에러 처리와 로깅을 구현해야 합니다.""",
                template="""[요청]
                새로운 API 엔드포인트 `{endpoint}` 를 구현하시오.

                [상세 요구사항]
                - HTTP 메소드: {method}
                - 설명: {description}
                - 입력 파라미터: {params}
                - 출력: {output}
                - 기타: {other_requirements}""",
                parameters=["endpoint", "method", "description", "params", "output", "other_requirements"],
                tags=["api", "fastapi", "backend"]
            ),
            PromptTemplate(
                name="code_review",
                description="코드 리뷰 수행",
                system_message="""당신은 경험 많은 시니어 개발자입니다.
                코드의 품질, 가독성, 성능, 보안을 중점적으로 검토하고
                구체적인 개선 제안을 제시해야 합니다.""",
                template="""[코드 리뷰 요청]
                아래 코드를 검토하고 개선점을 제안하시오.

                [코드]
                {code}

                [컨텍스트]
                {context}

                다음 관점에서 검토해 주세요:
                1. 코드 품질 및 가독성
                2. 성능 및 확장성
                3. 보안 및 안정성
                4. 테스트 커버리지""",
                parameters=["code", "context"],
                tags=["review", "quality", "security"]
            ),
            PromptTemplate(
                name="bug_fix",
                description="버그 수정",
                system_message="""당신은 문제 해결 전문가입니다.
                버그의 근본 원인을 파악하고, 안정적인 해결책을 제시해야 합니다.
                임시방편이 아닌 장기적인 관점의 수정을 제안하세요.""",
                template="""[버그 리포트]
                {bug_description}

                [에러 로그]
                {error_log}

                [관련 코드]
                {code}

                [컨텍스트]
                {context}

                다음 단계로 분석해 주세요:
                1. 근본 원인 분석
                2. 해결 방안 제시
                3. 재발 방지 대책""",
                parameters=["bug_description", "error_log", "code", "context"],
                tags=["bugfix", "debugging"]
            ),
            PromptTemplate(
                name="refactoring",
                description="코드 리팩토링",
                system_message="""당신은 리팩토링 전문가입니다.
                코드의 구조를 개선하면서도 기존 기능은 그대로 유지해야 합니다.
                SOLID 원칙과 디자인 패턴을 적절히 활용하세요.""",
                template="""[리팩토링 요청]
                {refactoring_goal}

                [현재 코드]
                {code}

                [컨텍스트]
                {context}

                다음 단계로 진행해 주세요:
                1. 현재 구조 분석
                2. 개선점 식별
                3. 리팩토링 계획 수립
                4. 단계별 변경 제안""",
                parameters=["refactoring_goal", "code", "context"],
                tags=["refactoring", "improvement"]
            )
        ]

        for template in templates:
            await self.shared_memory.store(
                key=f"prompt_template:{template.name}",
                value=template.dict(),
                type="prompt_template",
                tags={"prompt_template"} | set(template.tags),
                ttl=None  # 영구 보관
            )

    async def get_template(self, name: str) -> Optional[PromptTemplate]:
        """프롬프트 템플릿 조회

        Args:
            name: 템플릿 이름

        Returns:
            PromptTemplate: 프롬프트 템플릿 (없으면 None)
        """
        result = await self.shared_memory.get(f"prompt_template:{name}")
        if result:
            return PromptTemplate(**result)
        return None

    async def create_template(self, template: PromptTemplate) -> bool:
        """새로운 프롬프트 템플릿 생성

        Args:
            template: 프롬프트 템플릿

        Returns:
            bool: 성공 여부
        """
        try:
            await self.shared_memory.store(
                key=f"prompt_template:{template.name}",
                value=template.dict(),
                type="prompt_template",
                tags={"prompt_template"} | set(template.tags),
                ttl=None
            )
            return True
        except Exception as e:
            logger.error(f"템플릿 생성 실패: {str(e)}")
            return False

    async def update_template(self, template: PromptTemplate) -> bool:
        """프롬프트 템플릿 업데이트

        Args:
            template: 프롬프트 템플릿

        Returns:
            bool: 성공 여부
        """
        try:
            template.updated_at = datetime.now()
            await self.shared_memory.store(
                key=f"prompt_template:{template.name}",
                value=template.dict(),
                type="prompt_template",
                tags={"prompt_template"} | set(template.tags),
                ttl=None
            )
            return True
        except Exception as e:
            logger.error(f"템플릿 업데이트 실패: {str(e)}")
            return False

    async def delete_template(self, name: str) -> bool:
        """프롬프트 템플릿 삭제

        Args:
            name: 템플릿 이름

        Returns:
            bool: 성공 여부
        """
        try:
            await self.shared_memory.delete(f"prompt_template:{name}")
            return True
        except Exception as e:
            logger.error(f"템플릿 삭제 실패: {str(e)}")
            return False

    async def search_templates(self, tags: Optional[List[str]] = None) -> List[PromptTemplate]:
        """프롬프트 템플릿 검색

        Args:
            tags: 검색할 태그 목록

        Returns:
            List[PromptTemplate]: 검색된 템플릿 목록
        """
        search_tags = {"prompt_template"}
        if tags:
            search_tags.update(tags)

        results = await self.shared_memory.search(
            type="prompt_template",
            tags=search_tags
        )

        return [PromptTemplate(**result) for result in results]

    async def generate_prompt(
        self,
        template_name: str,
        parameters: Dict[str, str],
        additional_context: Optional[str] = None
    ) -> str:
        """프롬프트 생성

        Args:
            template_name: 템플릿 이름
            parameters: 파라미터 값
            additional_context: 추가 컨텍스트

        Returns:
            str: 생성된 프롬프트
        """
        template = await self.get_template(template_name)
        if not template:
            raise ValueError(f"템플릿을 찾을 수 없음: {template_name}")

        # 시스템 컨텍스트 추가
        system_context = await self.context_manager.get_system_context()
        if additional_context:
            system_context = f"{system_context}\n\n{additional_context}"

        # 프롬프트 생성
        prompt = template.template.format(**parameters)
        return f"{system_context}\n\n{prompt}"

    async def execute_prompt(
        self,
        template_name: str,
        parameters: Dict[str, str],
        additional_context: Optional[str] = None,
        **llm_kwargs
    ) -> str:
        """프롬프트 실행

        Args:
            template_name: 템플릿 이름
            parameters: 파라미터 값
            additional_context: 추가 컨텍스트
            **llm_kwargs: LLM 설정 (temperature 등)

        Returns:
            str: LLM 응답
        """
        template = await self.get_template(template_name)
        if not template:
            raise ValueError(f"템플릿을 찾을 수 없음: {template_name}")

        prompt = await self.generate_prompt(template_name, parameters, additional_context)
        return await self.llm.generate(prompt, template.system_message, **llm_kwargs) 