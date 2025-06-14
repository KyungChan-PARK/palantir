from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """모든 에이전트의 공통 인터페이스"""
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def process(self, *args, **kwargs):
        """에이전트의 핵심 작업을 수행한다."""
        pass 