from typing import Any, Dict, Optional

from .base import BaseAgent


class ReviewerAgent(BaseAgent):
    async def review_code(self, code: str) -> Any:
        return await self.think(code)

    async def check_security(self, code: str) -> Any:
        return await self.think(code)

    def process(self, input_data: Any, state: Optional[Dict[str, Any]] = None) -> Any:
        return input_data
