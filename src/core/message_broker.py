"""메시지 브로커 시스템"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import uuid
import logging

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """메시지 유형"""
    TASK = "task"                 # 작업 요청/응답
    EVENT = "event"               # 이벤트 알림
    CONTROL = "control"           # 제어 명령
    STATUS = "status"             # 상태 업데이트
    METRIC = "metric"             # 메트릭 데이터
    LOG = "log"                   # 로그 메시지


class MessagePriority(Enum):
    """메시지 우선순위"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class Message:
    """메시지 모델"""
    id: str
    type: MessageType
    sender: str
    recipients: List[str]
    subject: str
    content: Any
    priority: MessagePriority
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    timestamp: datetime = datetime.now()
    metadata: Dict[str, Any] = None

    @property
    def age(self) -> float:
        """메시지 경과 시간(초)"""
        return (datetime.now() - self.timestamp).total_seconds()


class MessageBroker:
    """메시지 브로커"""

    def __init__(self):
        """브로커 초기화"""
        self.subscribers: Dict[str, Set[Callable]] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.tasks: List[asyncio.Task] = []

    async def start(self):
        """브로커 시작"""
        if self.running:
            return

        self.running = True
        self.tasks.append(asyncio.create_task(self._process_messages()))
        logger.info("Message broker started")

    async def stop(self):
        """브로커 중지"""
        self.running = False
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        logger.info("Message broker stopped")

    def subscribe(self, topic: str, callback: Callable[[Message], None]):
        """토픽 구독
        
        Args:
            topic: 구독할 토픽
            callback: 메시지 수신 시 호출할 콜백 함수
        """
        if topic not in self.subscribers:
            self.subscribers[topic] = set()
        self.subscribers[topic].add(callback)
        logger.debug(f"Subscribed to topic: {topic}")

    def unsubscribe(self, topic: str, callback: Callable[[Message], None]):
        """토픽 구독 해제"""
        if topic in self.subscribers:
            self.subscribers[topic].discard(callback)
            if not self.subscribers[topic]:
                del self.subscribers[topic]
            logger.debug(f"Unsubscribed from topic: {topic}")

    async def publish(self, message: Message):
        """메시지 발행"""
        await self.message_queue.put(message)
        logger.debug(f"Published message: {message.id}")

    async def _process_messages(self):
        """메시지 처리 루프"""
        while self.running:
            try:
                message = await self.message_queue.get()
                await self._deliver_message(message)
                self.message_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def _deliver_message(self, message: Message):
        """메시지 전달"""
        delivered = False

        # 특정 수신자가 지정된 경우
        if message.recipients:
            for recipient in message.recipients:
                topic = f"{recipient}.{message.type.value}"
                if topic in self.subscribers:
                    for callback in self.subscribers[topic]:
                        try:
                            await asyncio.create_task(self._call_callback(callback, message))
                            delivered = True
                        except Exception as e:
                            logger.error(f"Error delivering message to {recipient}: {e}")

        # 브로드캐스트 메시지
        else:
            topic = message.type.value
            if topic in self.subscribers:
                for callback in self.subscribers[topic]:
                    try:
                        await asyncio.create_task(self._call_callback(callback, message))
                        delivered = True
                    except Exception as e:
                        logger.error(f"Error broadcasting message: {e}")

        if not delivered:
            logger.warning(f"No subscribers for message: {message.id}")

    async def _call_callback(self, callback: Callable[[Message], None], message: Message):
        """콜백 함수 호출"""
        if asyncio.iscoroutinefunction(callback):
            await callback(message)
        else:
            callback(message)


class MessageBuilder:
    """메시지 빌더"""

    def __init__(self):
        self.reset()

    def reset(self):
        """빌더 초기화"""
        self._message = {
            "id": str(uuid.uuid4()),
            "type": None,
            "sender": None,
            "recipients": [],
            "subject": "",
            "content": None,
            "priority": MessagePriority.NORMAL,
            "correlation_id": None,
            "reply_to": None,
            "timestamp": datetime.now(),
            "metadata": {}
        }
        return self

    def with_type(self, message_type: MessageType):
        """메시지 유형 설정"""
        self._message["type"] = message_type
        return self

    def from_sender(self, sender: str):
        """발신자 설정"""
        self._message["sender"] = sender
        return self

    def to_recipients(self, recipients: List[str]):
        """수신자 설정"""
        self._message["recipients"] = recipients
        return self

    def with_subject(self, subject: str):
        """제목 설정"""
        self._message["subject"] = subject
        return self

    def with_content(self, content: Any):
        """내용 설정"""
        self._message["content"] = content
        return self

    def with_priority(self, priority: MessagePriority):
        """우선순위 설정"""
        self._message["priority"] = priority
        return self

    def with_correlation_id(self, correlation_id: str):
        """상관 ID 설정"""
        self._message["correlation_id"] = correlation_id
        return self

    def reply_to(self, reply_to: str):
        """응답 대상 설정"""
        self._message["reply_to"] = reply_to
        return self

    def with_metadata(self, metadata: Dict[str, Any]):
        """메타데이터 설정"""
        self._message["metadata"] = metadata
        return self

    def build(self) -> Message:
        """메시지 생성"""
        if not self._message["type"]:
            raise ValueError("Message type is required")
        if not self._message["sender"]:
            raise ValueError("Sender is required")

        return Message(**self._message) 