"""코드 리뷰 담당 에이전트"""

from typing import Any, Dict, List

from src.agents.base_agent import AgentConfig, BaseAgent
from palantir.services.mcp.llm_mcp import LLMMCP


class ReviewerAgent(BaseAgent):
    """코드 리뷰 담당 에이전트"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.llm = LLMMCP()

    def _initialize(self) -> None:
        """에이전트 초기화"""
        pass

    async def process(self, input_data: Any) -> Any:
        """코드 리뷰 수행"""
        # 1. 작업 정보 검색
        task = input_data.get("task", "")
        analysis = await self.retrieve_memory(f"task_analysis:{task}")
        implementation = await self.retrieve_memory(f"implementation:{task}")
        tests = await self.retrieve_memory(f"tests:{task}")
        
        # 2. 코드 리뷰 수행
        review = await self.review_code({
            "task": task,
            "analysis": analysis,
            "implementation": implementation,
            "tests": tests
        })
        
        # 3. 리뷰 결과를 메모리에 저장
        await self.store_memory(
            key=f"review:{task}",
            value=review,
            type="review",
            tags={"task", "review", self.config.name},
            metadata={"task": task}
        )
        
        # 4. 테스트 실행
        test_results = await self.run_tests({
            "code": implementation["code"],
            "tests": tests["tests"]
        })
        
        # 5. 테스트 결과를 메모리에 저장
        await self.store_memory(
            key=f"test_results:{task}",
            value=test_results,
            type="test_results",
            tags={"task", "test_results", self.config.name},
            metadata={"task": task}
        )
        
        # 6. 컨텍스트 업데이트
        self.update_agent_context("last_task", task)
        self.update_global_context("current_review", review)
        
        return {
            "review": review,
            "test_results": test_results
        }

    async def review_code(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """코드 리뷰"""
        # 1. 이전 리뷰 검색
        task = input_data["task"]
        previous_reviews = await self.search_memory({"task", "review"})
        
        # 2. 프롬프트 생성
        prompt = (
            "아래 코드를 리뷰하고 개선사항을 제안하세요.\n"
            f"작업: {task}\n"
            "---\n"
            f"작업 분석:\n{input_data.get('analysis', '')}\n"
            "---\n"
            f"구현:\n{input_data.get('implementation', {}).get('code', '')}\n"
            "---\n"
            f"테스트:\n{input_data.get('tests', {}).get('tests', '')}\n"
            "---\n"
            "이전 리뷰:\n"
            f"{previous_reviews}\n"
            "---\n"
            "다음 사항을 검토하세요:\n"
            "1. 코드 품질\n"
            "2. 테스트 커버리지\n"
            "3. 성능\n"
            "4. 보안\n"
            "5. 유지보수성\n"
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
            "review": response.get("text", ""),
            "timestamp": response.get("timestamp", "")
        }

    async def run_tests(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """테스트 실행"""
        # 1. 이전 테스트 결과 검색
        code = input_data["code"]
        tests = input_data["tests"]
        previous_results = await self.search_memory({"task", "test_results"})
        
        # 2. 프롬프트 생성
        prompt = (
            "아래 코드와 테스트를 실행하고 결과를 분석하세요.\n"
            f"코드:\n{code}\n"
            "---\n"
            f"테스트:\n{tests}\n"
            "---\n"
            "이전 테스트 결과:\n"
            f"{previous_results}\n"
            "---\n"
            "다음 사항을 포함하세요:\n"
            "1. 테스트 성공/실패\n"
            "2. 커버리지 분석\n"
            "3. 성능 측정\n"
            "4. 메모리 사용량\n"
            "5. 개선 제안\n"
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
            "tests": tests,
            "results": response.get("text", ""),
            "timestamp": response.get("timestamp", "")
        }

    async def validate(self, output: Any) -> bool:
        # 검토 결과 검증 로직 (스켈레톤)
        return True
