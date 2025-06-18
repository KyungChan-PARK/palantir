from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import asyncio
import logging
from datetime import datetime

from pydantic import BaseModel, Field

from src.core.message_broker import Message, MessageBroker, MessageBuilder, MessageType, MessagePriority
from palantir.core.shared_memory import SharedMemory
from palantir.core.context_manager import ContextManager
from palantir.core.metrics import (
    TASK_PROCESSING_TIME,
    TASK_COUNTER,
    MEMORY_USAGE,
    SHARED_MEMORY_SIZE,
    LLM_CALLS,
    LLM_TOKENS,
    LLM_LATENCY,
    AGENT_STATUS,
    AGENT_ERRORS,
    TASK_SUCCESS_RATE,
    RESPONSE_QUALITY,
    CPU_USAGE,
    DISK_IO,
    CONTEXT_SIZE,
    CONTEXT_UPDATES
)
from src.core.profiler import PerformanceProfiler

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """에이전트 설정을 위한 기본 모델"""

    name: str = Field(..., description="에이전트 이름")
    description: str = Field(..., description="에이전트 설명")
    model: str = Field(..., description="사용할 LLM 모델")
    temperature: float = Field(default=0.7, description="생성 온도")
    max_tokens: int = Field(default=2000, description="최대 토큰 수")
    system_prompt: str = Field(..., description="시스템 프롬프트")


class BaseAgent(ABC):
    """모든 에이전트의 기본 클래스"""

    def __init__(
        self,
        agent_id: str,
        message_broker: MessageBroker,
        profiler: Optional[PerformanceProfiler] = None,
    ):
        """
        Args:
            agent_id: 에이전트 ID
            message_broker: 메시지 브로커
            profiler: 성능 프로파일러
        """
        self.agent_id = agent_id
        self.message_broker = message_broker
        self.profiler = profiler or PerformanceProfiler()
        self.running = False
        self.tasks: List[asyncio.Task] = []
        self.current_task_id: Optional[str] = None
        self.shared_memory = SharedMemory()
        self.context_manager = ContextManager()
        self._initialize()
        self._update_status("initialized")
        self._setup_message_handlers()

    def _initialize(self) -> None:
        """에이전트 초기화"""
        pass

    def _setup_message_handlers(self):
        """메시지 핸들러 설정"""
        # 작업 메시지 구독
        self.message_broker.subscribe(
            f"{self.agent_id}.{MessageType.TASK.value}",
            self._handle_task_message
        )

        # 제어 메시지 구독
        self.message_broker.subscribe(
            f"{self.agent_id}.{MessageType.CONTROL.value}",
            self._handle_control_message
        )

        # 이벤트 메시지 구독
        self.message_broker.subscribe(
            MessageType.EVENT.value,
            self._handle_event_message
        )

    async def _handle_task_message(self, message: Message):
        """작업 메시지 처리"""
        try:
            # 작업 처리
            result = await self.process(message.content)

            # 응답 메시지 생성
            response = (
                MessageBuilder()
                .with_type(MessageType.TASK)
                .from_sender(self.agent_id)
                .to_recipients([message.sender])
                .with_subject(f"Re: {message.subject}")
                .with_content(result)
                .with_correlation_id(message.id)
                .with_priority(message.priority)
                .build()
            )

            # 응답 전송
            await self.message_broker.publish(response)

        except Exception as e:
            logger.error(f"Error processing task message: {e}")
            # 에러 응답 전송
            error_response = (
                MessageBuilder()
                .with_type(MessageType.TASK)
                .from_sender(self.agent_id)
                .to_recipients([message.sender])
                .with_subject(f"Error: {message.subject}")
                .with_content({"error": str(e)})
                .with_correlation_id(message.id)
                .with_priority(MessagePriority.HIGH)
                .build()
            )
            await self.message_broker.publish(error_response)

    async def _handle_control_message(self, message: Message):
        """제어 메시지 처리"""
        command = message.content.get("command")
        if command == "stop":
            await self.stop()
        elif command == "pause":
            await self.pause()
        elif command == "resume":
            await self.resume()
        else:
            logger.warning(f"Unknown control command: {command}")

    async def _handle_event_message(self, message: Message):
        """이벤트 메시지 처리"""
        event_type = message.content.get("type")
        event_data = message.content.get("data")
        logger.info(f"Received event: {event_type} with data: {event_data}")

    async def start(self):
        """에이전트 시작"""
        if self.running:
            return

        self.running = True
        self.tasks.append(
            asyncio.create_task(self._process_messages())
        )
        logger.info(f"Agent {self.agent_id} started")

    async def stop(self):
        """에이전트 중지"""
        self.running = False
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        logger.info(f"Agent {self.agent_id} stopped")

    async def pause(self):
        """에이전트 일시 중지"""
        self._update_status("paused")

    async def resume(self):
        """에이전트 재개"""
        self._update_status("running")

    def _update_status(self, status: str):
        """상태 업데이트"""
        AGENT_STATUS.labels(agent_name=self.agent_id, status=status).set(1)
        AGENT_STATUS.labels(agent_name=self.agent_id, status="other").set(0)

    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """입력 데이터를 처리하는 메서드"""
        pass

    @abstractmethod
    async def validate(self, output: Any) -> bool:
        """출력 결과를 검증하는 메서드"""
        pass

    async def execute(self, input_data: Any) -> Any:
        """에이전트 실행 파이프라인"""
        result = await self.process(input_data)
        if await self.validate(result):
            return result
        raise ValueError("에이전트 실행 결과가 유효하지 않습니다.")

    def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 정보 반환"""
        return {
            "name": self.agent_id,
            "description": self.description,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    async def send_message(
        self,
        recipients: List[str],
        subject: str,
        content: Any,
        message_type: MessageType = MessageType.TASK,
        priority: MessagePriority = MessagePriority.NORMAL,
    ):
        """메시지 전송"""
        message = (
            MessageBuilder()
            .with_type(message_type)
            .from_sender(self.agent_id)
            .to_recipients(recipients)
            .with_subject(subject)
            .with_content(content)
            .with_priority(priority)
            .build()
        )
        await self.message_broker.publish(message)

    async def broadcast_event(
        self,
        event_type: str,
        event_data: Any,
        priority: MessagePriority = MessagePriority.NORMAL,
    ):
        """이벤트 브로드캐스트"""
        message = (
            MessageBuilder()
            .with_type(MessageType.EVENT)
            .from_sender(self.agent_id)
            .with_subject(event_type)
            .with_content({
                "type": event_type,
                "data": event_data,
            })
            .with_priority(priority)
            .build()
        )
        await self.message_broker.publish(message)

    async def store_memory(
        self,
        key: str,
        value: Any,
        type: str,
        ttl: Optional[int] = None,
        tags: Optional[set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """메모리에 데이터 저장"""
        success = await self.shared_memory.store(
            key=key,
            value=value,
            type=type,
            ttl=ttl,
            tags=tags or set(),
            metadata=metadata or {}
        )
        
        # 메모리 사용량 메트릭 업데이트
        MEMORY_USAGE.labels(agent_name=self.agent_id).set(
            psutil.Process().memory_info().rss
        )
        SHARED_MEMORY_SIZE.labels(agent_name=self.agent_id).set(
            len(await self.shared_memory.get_all_keys())
        )
        
        return success

    async def retrieve_memory(
        self,
        key: str,
        default: Any = None
    ) -> Optional[Any]:
        """메모리에서 데이터 검색"""
        entry = await self.shared_memory.retrieve(key, default)
        return entry.value if entry else default

    async def search_memory(
        self,
        tags: set[str],
        match_all: bool = True
    ) -> list[Any]:
        """태그로 메모리 검색"""
        entries = await self.shared_memory.search_by_tags(tags, match_all)
        return [entry.value for entry in entries]

    def get_agent_context(self) -> Dict[str, Any]:
        """에이전트 컨텍스트 조회"""
        context = self.context_manager.get_agent_context(self.agent_id)
        CONTEXT_UPDATES.labels(
            agent_name=self.agent_id,
            context_type="agent",
            operation="get"
        ).inc()
        CONTEXT_SIZE.labels(
            agent_name=self.agent_id,
            context_type="agent"
        ).set(len(str(context)))
        return context

    def update_agent_context(self, key: str, value: Any) -> None:
        """에이전트 컨텍스트 업데이트"""
        self.context_manager.update_agent_context(self.agent_id, key, value)
        CONTEXT_UPDATES.labels(
            agent_name=self.agent_id,
            context_type="agent",
            operation="update"
        ).inc()

    def get_global_context(self) -> Dict[str, Any]:
        """글로벌 컨텍스트 조회"""
        context = self.context_manager.get_global_context()
        CONTEXT_UPDATES.labels(
            agent_name=self.agent_id,
            context_type="global",
            operation="get"
        ).inc()
        CONTEXT_SIZE.labels(
            agent_name=self.agent_id,
            context_type="global"
        ).set(len(str(context)))
        return context

    def update_global_context(self, key: str, value: Any) -> None:
        """글로벌 컨텍스트 업데이트"""
        self.context_manager.update_global_context(key, value)
        CONTEXT_UPDATES.labels(
            agent_name=self.agent_id,
            context_type="global",
            operation="update"
        ).inc()

    async def _record_task_metrics(
        self,
        task_type: str,
        start_time: float,
        success: bool,
        quality_metrics: Optional[Dict[str, float]] = None
    ) -> None:
        """작업 메트릭 기록"""
        # 처리 시간
        processing_time = time.time() - start_time
        TASK_PROCESSING_TIME.labels(
            agent_name=self.agent_id,
            task_type=task_type
        ).observe(processing_time)
        
        # 작업 카운터
        status = "success" if success else "failure"
        TASK_COUNTER.labels(
            agent_name=self.agent_id,
            task_type=task_type,
            status=status
        ).inc()
        
        # 성공률 업데이트
        total = TASK_COUNTER.labels(
            agent_name=self.agent_id,
            task_type=task_type,
            status="success"
        )._value.get() + TASK_COUNTER.labels(
            agent_name=self.agent_id,
            task_type=task_type,
            status="failure"
        )._value.get()
        
        if total > 0:
            success_rate = TASK_COUNTER.labels(
                agent_name=self.agent_id,
                task_type=task_type,
                status="success"
            )._value.get() / total
            TASK_SUCCESS_RATE.labels(agent_name=self.agent_id).set(success_rate)
        
        # 품질 메트릭 업데이트
        if quality_metrics:
            for metric_type, value in quality_metrics.items():
                RESPONSE_QUALITY.labels(
                    agent_name=self.agent_id,
                    metric_type=metric_type
                ).set(value)

    async def _record_llm_metrics(
        self,
        model: str,
        start_time: float,
        success: bool,
        prompt_tokens: int,
        completion_tokens: int
    ) -> None:
        """LLM 호출 메트릭 기록"""
        # 호출 카운터
        status = "success" if success else "failure"
        LLM_CALLS.labels(
            agent_name=self.agent_id,
            model=model,
            status=status
        ).inc()
        
        # 토큰 사용량
        LLM_TOKENS.labels(
            agent_name=self.agent_id,
            model=model,
            type="prompt"
        ).inc(prompt_tokens)
        LLM_TOKENS.labels(
            agent_name=self.agent_id,
            model=model,
            type="completion"
        ).inc(completion_tokens)
        
        # 지연 시간
        latency = time.time() - start_time
        LLM_LATENCY.labels(
            agent_name=self.agent_id,
            model=model
        ).observe(latency)

    def _record_error(self, error_type: str) -> None:
        """에러 메트릭 기록"""
        AGENT_ERRORS.labels(
            agent_name=self.agent_id,
            error_type=error_type
        ).inc()
        self._update_status("error")

    async def _process_messages(self):
        """메시지 처리"""
        while self.running:
            try:
                # 메시지 수신
                message = await self.message_broker.subscribe(
                    recipient=self.agent_id
                )

                if not message:
                    await asyncio.sleep(0.1)
                    continue

                # 작업 프로파일링 시작
                self.current_task_id = message.id
                self.profiler.start_task(
                    task_id=self.current_task_id,
                    agent_id=self.agent_id,
                )

                try:
                    # 메시지 유형별 처리
                    if message.type == MessageType.TASK:
                        await self._handle_task(message)
                    elif message.type == MessageType.CONTROL:
                        await self._handle_control(message)
                    elif message.type == MessageType.EVENT:
                        await self._handle_event(message)

                    # 작업 프로파일링 종료 (성공)
                    self.profiler.end_task(
                        task_id=self.current_task_id,
                        status="completed",
                    )

                except Exception as e:
                    # 작업 프로파일링 종료 (실패)
                    self.profiler.end_task(
                        task_id=self.current_task_id,
                        status="failed",
                    )
                    self.profiler.record_error(self.current_task_id)
                    logger.error(f"Error processing message: {e}")
                    await self._publish_error(str(e))

                finally:
                    self.current_task_id = None

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in message processing loop: {e}")
                await asyncio.sleep(1)

    async def _handle_task(self, message: Any):
        """작업 메시지 처리"""
        raise NotImplementedError

    async def _handle_control(self, message: Any):
        """제어 메시지 처리"""
        raise NotImplementedError

    async def _handle_event(self, message: Any):
        """이벤트 메시지 처리"""
        raise NotImplementedError

    async def _publish_result(self, result: Any):
        """결과 발행"""
        if not self.current_task_id:
            return

        message = (
            MessageBuilder()
            .with_type(MessageType.RESULT)
            .from_sender(self.agent_id)
            .with_subject("Task completed")
            .with_content({
                "task_id": self.current_task_id,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            })
            .build()
        )
        await self.message_broker.publish(message)

    async def _publish_error(self, error: str):
        """에러 발행"""
        if not self.current_task_id:
            return

        message = (
            MessageBuilder()
            .with_type(MessageType.ERROR)
            .from_sender(self.agent_id)
            .with_subject("Task failed")
            .with_content({
                "task_id": self.current_task_id,
                "error": error,
                "timestamp": datetime.now().isoformat(),
            })
            .build()
        )
        await self.message_broker.publish(message)

    async def _publish_status(self, status: str, details: Optional[Dict] = None):
        """상태 발행"""
        message = (
            MessageBuilder()
            .with_type(MessageType.STATUS)
            .from_sender(self.agent_id)
            .with_subject("Agent status update")
            .with_content({
                "status": status,
                "details": details or {},
                "timestamp": datetime.now().isoformat(),
            })
            .build()
        )
        await self.message_broker.publish(message)

    async def _record_llm_usage(self, tokens: int, latency: float):
        """LLM 사용량 기록"""
        if self.current_task_id:
            self.profiler.record_llm_call(
                task_id=self.current_task_id,
                tokens=tokens,
                latency=latency,
            )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 조회"""
        return self.profiler.get_agent_metrics(self.agent_id)

    def analyze_performance(self) -> Dict[str, Any]:
        """성능 분석"""
        return self.profiler.analyze_performance(self.agent_id)

    def get_optimization_suggestions(self) -> List[str]:
        """최적화 제안 조회"""
        analysis = self.analyze_performance()
        if not analysis:
            return []
        return self.profiler.get_optimization_suggestions(analysis)
