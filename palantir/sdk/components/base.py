from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Dict, Any

class ComponentMeta(BaseModel, ABC):
    id: str
    name: str
    params: Dict[str, Any] = {}

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """컴포넌트 실행 메서드 (구현 필수)"""
        pass 