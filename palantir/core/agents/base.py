"""
기본 에이전트 클래스
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAgent(ABC):
    """모든 에이전트의 기본 클래스"""

    def __init__(self, name: str):
        """
        에이전트 초기화

        Args:
            name: 에이전트 이름
        """
        self.name = name

    @abstractmethod
    def process(self, input_data: Any, state: Optional[Dict] = None) -> Any:
        """
        입력 데이터 처리

        Args:
            input_data: 처리할 입력 데이터
            state: 현재 상태 정보

        Returns:
            처리 결과
        """
        pass
