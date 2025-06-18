"""코드 개발 담당 에이전트"""

from typing import Any, Dict, List

from src.agents.base_agent import AgentConfig, BaseAgent
from palantir.services.mcp.llm_mcp import LLMMCP


class DeveloperAgent(BaseAgent):
    """코드 개발 담당 에이전트"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.llm = LLMMCP()

    def _initialize(self) -> None:
        """에이전트 초기화"""
        pass

    async def process(self, input_data: Any) -> Any:
        """코드 구현 및 테스트 작성"""
        # 1. 작업 분석 결과 검색
        task = input_data.get("task", "")
        analysis = await self.retrieve_memory(f"task_analysis:{task}")
        subtasks = await self.retrieve_memory(f"task_subtasks:{task}")
        
        # 2. 기능 구현
        implementation = await self.implement_feature({
            "task": task,
            "analysis": analysis,
            "subtasks": subtasks
        })
        
        # 3. 구현 결과를 메모리에 저장
        await self.store_memory(
            key=f"implementation:{task}",
            value=implementation,
            type="implementation",
            tags={"task", "implementation", self.config.name},
            metadata={"task": task}
        )
        
        # 4. 테스트 작성
        tests = await self.write_tests({"code": implementation["code"]})
        
        # 5. 테스트를 메모리에 저장
        await self.store_memory(
            key=f"tests:{task}",
            value=tests,
            type="tests",
            tags={"task", "tests", self.config.name},
            metadata={"task": task}
        )
        
        # 6. 컨텍스트 업데이트
        self.update_agent_context("last_task", task)
        self.update_global_context("current_implementation", implementation["code"])
        
        return {
            "implementation": implementation,
            "tests": tests
        }

    async def implement_feature(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """기능 구현"""
        # 1. 이전 구현 검색
        task = input_data["task"]
        previous_implementations = await self.search_memory({"task", "implementation"})
        
        # 2. 프롬프트 생성
        prompt = (
            "아래 작업을 구현하는 파이썬 코드를 작성하세요.\n"
            f"작업: {task}\n"
            "---\n"
            f"작업 분석:\n{input_data.get('analysis', '')}\n"
            "---\n"
            f"하위 작업:\n{input_data.get('subtasks', [])}\n"
            "---\n"
            "이전 구현:\n"
            f"{previous_implementations}\n"
            "---\n"
            "다음 사항을 준수하세요:\n"
            "1. PEP8 스타일 가이드\n"
            "2. 타입 힌트 사용\n"
            "3. 문서화 주석 포함\n"
            "4. 에러 처리\n"
            "5. 로깅\n"
        )
        
        # 3. LLM 호출
        response = await self.llm.generate(
            prompt=prompt,
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        return {
            "task": task,
            "code": response.get("text", ""),
            "timestamp": response.get("timestamp", "")
        }

    async def write_tests(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """테스트 작성"""
        # 1. 이전 테스트 검색
        code = input_data["code"]
        previous_tests = await self.search_memory({"task", "tests"})
        
        # 2. 프롬프트 생성
        prompt = (
            "아래 코드에 대한 테스트 코드를 작성하세요.\n"
            f"코드:\n{code}\n"
            "---\n"
            "이전 테스트:\n"
            f"{previous_tests}\n"
            "---\n"
            "다음 사항을 준수하세요:\n"
            "1. pytest 사용\n"
            "2. 단위 테스트 작성\n"
            "3. 엣지 케이스 포함\n"
            "4. 모킹 사용\n"
            "5. 문서화 주석\n"
        )
        
        # 3. LLM 호출
        response = await self.llm.generate(
            prompt=prompt,
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        return {
            "code": code,
            "tests": response.get("text", ""),
            "timestamp": response.get("timestamp", "")
        }

    async def validate(self, output: Any) -> bool:
        # 코드 검증 로직 (스켈레톤)
        return True
