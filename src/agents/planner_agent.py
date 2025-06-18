"""작업 계획 담당 에이전트"""

from typing import Any, Dict, List

from src.agents.base_agent import AgentConfig, BaseAgent
from palantir.services.mcp.llm_mcp import LLMMCP


class PlannerAgent(BaseAgent):
    """작업 계획 담당 에이전트"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.llm = LLMMCP()

    def _initialize(self) -> None:
        """에이전트 초기화"""
        pass

    async def process(self, input_data: Any) -> Any:
        """작업 분석 및 계획 수립"""
        # 1. 작업 분석
        analysis = await self.analyze_task(input_data["task"])
        
        # 2. 분석 결과를 메모리에 저장
        await self.store_memory(
            key=f"task_analysis:{input_data['task']}",
            value=analysis,
            type="analysis",
            tags={"task", "analysis", self.config.name},
            metadata={"task": input_data["task"]}
        )
        
        # 3. 하위 작업 생성
        subtasks = await self.create_subtasks({"task": input_data["task"]})
        
        # 4. 하위 작업을 메모리에 저장
        await self.store_memory(
            key=f"task_subtasks:{input_data['task']}",
            value=subtasks,
            type="subtasks",
            tags={"task", "subtasks", self.config.name},
            metadata={"task": input_data["task"]}
        )
        
        # 5. 컨텍스트 업데이트
        self.update_agent_context("last_task", input_data["task"])
        self.update_global_context("current_task", input_data["task"])
        
        return {
            "analysis": analysis,
            "subtasks": subtasks
        }

    async def analyze_task(self, task: str) -> Dict[str, Any]:
        """작업 분석"""
        # 1. 이전 분석 결과 검색
        previous_analysis = await self.search_memory({"task", "analysis"})
        
        # 2. 프롬프트 생성
        prompt = (
            "아래 작업을 분석하여 필요한 단계와 고려사항을 정리하세요.\n"
            f"작업: {task}\n"
            "---\n"
            "이전 분석 결과:\n"
            f"{previous_analysis}\n"
            "---\n"
            "1. 필요한 단계\n"
            "2. 고려사항\n"
            "3. 예상 소요 시간\n"
            "4. 필요한 리소스\n"
            "5. 위험 요소\n"
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
            "analysis": response.get("text", ""),
            "timestamp": response.get("timestamp", "")
        }

    async def create_subtasks(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """하위 작업 생성"""
        # 1. 작업 분석 결과 검색
        task = input_data["task"]
        analysis = await self.retrieve_memory(f"task_analysis:{task}")
        
        # 2. 프롬프트 생성
        prompt = (
            "아래 작업을 수행하기 위한 하위 작업 목록을 생성하세요.\n"
            f"작업: {task}\n"
            "---\n"
            f"작업 분석:\n{analysis}\n"
            "---\n"
            "각 하위 작업은 다음 형식으로 작성하세요:\n"
            "{\n"
            '  "id": "작업 ID",\n'
            '  "title": "작업 제목",\n'
            '  "description": "작업 설명",\n'
            '  "priority": 1-5 (1이 가장 높음),\n'
            '  "estimated_hours": 예상 소요 시간(시간 단위)\n'
            "}\n"
        )
        
        # 3. LLM 호출
        response = await self.llm.generate(
            prompt=prompt,
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        # 4. 결과 파싱
        import json
        try:
            subtasks = json.loads(response.get("text", "[]"))
            if not isinstance(subtasks, list):
                subtasks = [subtasks]
        except Exception:
            subtasks = []
        
        return subtasks

    async def validate(self, output: Any) -> bool:
        # 결과 검증 로직 (스켈레톤)
        return True

    def plan_tasks(self, input_data: Any) -> List[Dict[str, Any]]:
        # 입력을 여러 Task로 분해 (스켈레톤)
        return [{"subtask": input_data}]  # 실제로는 더 세분화
