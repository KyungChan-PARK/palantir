from typing import Any, Dict, Optional

from .base import BaseAgent


class PlannerAgent(BaseAgent):
    async def analyze_task(self, task: str) -> Any:
        return await self.think(task)

    async def create_subtasks(self, task: str) -> Any:
        return await self.think(task)

    def process(self, input_data: Any, state: Optional[Dict[str, Any]] = None) -> Any:
        return input_data
