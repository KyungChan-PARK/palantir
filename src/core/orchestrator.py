"""개선된 멀티에이전트 오케스트레이션 시스템"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from src.core.message_broker import MessageBroker, MessageBuilder, MessageType, MessagePriority
from src.core.dependency_graph import DependencyGraph
from src.core.shared_memory import SharedMemory
from src.core.context_manager import ContextManager
from src.agents.base_agent import AgentConfig
from src.agents.planner_agent import PlannerAgent
from src.agents.developer_agent import DeveloperAgent
from src.agents.reviewer_agent import ReviewerAgent
from src.agents.self_improvement_agent import SelfImprovementAgent

logger = logging.getLogger(__name__)


class Orchestrator:
    """개선된 멀티에이전트 오케스트레이터"""

    def __init__(
        self,
        execution_mode: str = "parallel",
        max_concurrent_tasks: int = 5,
        task_timeout: int = 300,
        performance_threshold: float = 0.8,
    ):
        # 시스템 컴포넌트 초기화
        self.message_broker = MessageBroker()
        self.dependency_graph = DependencyGraph()
        self.shared_memory = SharedMemory()
        self.context_manager = ContextManager()
        self.execution_mode = execution_mode
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_timeout = task_timeout
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)

        # 에이전트 초기화
        self.agents = {
            "planner": PlannerAgent(
                AgentConfig(
                    name="planner",
                    description="작업 계획 수립",
                    model="gpt-4",
                    system_prompt="작업을 분석하고 계획을 수립하는 에이전트입니다.",
                )
            ),
            "developer": DeveloperAgent(
                AgentConfig(
                    name="developer",
                    description="코드 구현",
                    model="gpt-4",
                    system_prompt="계획에 따라 코드를 구현하는 에이전트입니다.",
                )
            ),
            "reviewer": ReviewerAgent(
                AgentConfig(
                    name="reviewer",
                    description="코드 검토",
                    model="gpt-4",
                    system_prompt="구현된 코드를 검토하는 에이전트입니다.",
                )
            ),
            "self_improver": SelfImprovementAgent(
                AgentConfig(
                    name="self_improver",
                    description="자가 개선",
                    model="gpt-4",
                    system_prompt="시스템의 성능을 모니터링하고 개선하는 에이전트입니다.",
                )
            ),
        }

        # 의존성 그래프 구성
        self._setup_dependency_graph()
        self._setup_message_handlers()

    def _setup_dependency_graph(self):
        """의존성 그래프 설정"""
        # 에이전트 노드 추가
        for name, agent in self.agents.items():
            self.dependency_graph.add_agent(
                agent_id=name,
                name=agent.config.name,
                role=agent.config.description,
            )

        # 의존성 관계 추가
        self.dependency_graph.add_dependency("developer", "planner")
        self.dependency_graph.add_dependency("reviewer", "developer")
        self.dependency_graph.add_dependency("self_improver", "reviewer")

    def _setup_message_handlers(self):
        """메시지 핸들러 설정"""
        # 작업 완료 이벤트 구독
        self.message_broker.subscribe(
            MessageType.TASK.value,
            self._handle_task_completion
        )

        # 에이전트 상태 변경 이벤트 구독
        self.message_broker.subscribe(
            MessageType.STATUS.value,
            self._handle_status_change
        )

        # 에러 이벤트 구독
        self.message_broker.subscribe(
            MessageType.EVENT.value,
            self._handle_error_event
        )

    async def start(self):
        """오케스트레이터 시작"""
        logger.info("Starting orchestrator")
        await self.message_broker.start()
        
        # 모든 에이전트 시작
        for agent in self.agents.values():
            await agent.start()

        # 시작 이벤트 브로드캐스트
        await self._broadcast_system_event(
            "system_start",
            {"timestamp": datetime.utcnow().isoformat()}
        )

    async def stop(self):
        """오케스트레이터 중지"""
        logger.info("Stopping orchestrator")
        
        # 중지 이벤트 브로드캐스트
        await self._broadcast_system_event(
            "system_stop",
            {"timestamp": datetime.utcnow().isoformat()}
        )

        # 모든 에이전트 중지
        for agent in self.agents.values():
            await agent.stop()

        await self.message_broker.stop()

    async def submit_task(self, task_data: Dict[str, Any]) -> str:
        """작업 제출"""
        task_id = str(uuid4())
        logger.info(f"Submitting task {task_id}")

        # Planner에게 작업 전송
        await self.agents["planner"].send_message(
            recipients=["planner"],
            subject=f"New task: {task_id}",
            content=task_data,
            message_type=MessageType.TASK,
            priority=MessagePriority.NORMAL,
        )

        return task_id

    async def _handle_task_completion(self, message: Message):
        """작업 완료 처리"""
        agent_id = message.sender
        next_agents = list(self.dependency_graph.get_dependents(agent_id))

        if next_agents:
            # 다음 에이전트에게 작업 전달
            for next_agent in next_agents:
                await self.agents[next_agent].send_message(
                    recipients=[next_agent],
                    subject=f"Continue task: {message.correlation_id}",
                    content=message.content,
                    message_type=MessageType.TASK,
                    priority=message.priority,
                )
        else:
            # 최종 결과 처리
            logger.info(f"Task {message.correlation_id} completed")
            await self._broadcast_system_event(
                "task_completed",
                {
                    "task_id": message.correlation_id,
                    "result": message.content,
                }
            )

    async def _handle_status_change(self, message: Message):
        """상태 변경 처리"""
        agent_id = message.sender
        new_status = message.content["status"]
        
        # 의존성 그래프 업데이트
        self.dependency_graph.update_agent_status(
            agent_id=agent_id,
            status=new_status,
        )

        # 상태 변경 이벤트 브로드캐스트
        await self._broadcast_system_event(
            "agent_status_changed",
            {
                "agent_id": agent_id,
                "status": new_status,
            }
        )

    async def _handle_error_event(self, message: Message):
        """에러 이벤트 처리"""
        if message.content["type"] == "error":
            error_data = message.content["data"]
            logger.error(f"Error in agent {message.sender}: {error_data}")

            # 에러 복구 시도
            await self._attempt_error_recovery(message.sender, error_data)

    async def _attempt_error_recovery(self, agent_id: str, error_data: Dict[str, Any]):
        """에러 복구 시도"""
        # Self-Improver에게 에러 복구 요청
        await self.agents["self_improver"].send_message(
            recipients=["self_improver"],
            subject=f"Error recovery: {agent_id}",
            content={
                "agent_id": agent_id,
                "error": error_data,
            },
            message_type=MessageType.TASK,
            priority=MessagePriority.HIGH,
        )

    async def _broadcast_system_event(self, event_type: str, event_data: Dict[str, Any]):
        """시스템 이벤트 브로드캐스트"""
        message = (
            MessageBuilder()
            .with_type(MessageType.EVENT)
            .from_sender("orchestrator")
            .with_subject(event_type)
            .with_content({
                "type": event_type,
                "data": event_data,
                "timestamp": datetime.utcnow().isoformat(),
            })
            .with_priority(MessagePriority.NORMAL)
            .build()
        )
        await self.message_broker.publish(message)

    def get_execution_plan(self) -> List[str]:
        """실행 계획 조회"""
        return self.dependency_graph.get_execution_order()

    def get_critical_path(self) -> List[str]:
        """크리티컬 패스 조회"""
        return self.dependency_graph.get_critical_path()

    def get_bottlenecks(self) -> List[str]:
        """병목 지점 조회"""
        return self.dependency_graph.get_bottlenecks()

    def validate_dependencies(self) -> List[tuple]:
        """의존성 유효성 검증"""
        return self.dependency_graph.validate_dependencies()
