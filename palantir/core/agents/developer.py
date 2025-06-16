from typing import Any, Dict, Optional

from .base import BaseAgent


class DeveloperAgent(BaseAgent):
    async def implement_feature(self, feature: str) -> Any:
        return await self.think(feature)

    async def write_tests(self, code: str) -> Any:
        return await self.think(code)

    def process(self, input_data: Any, state: Optional[Dict[str, Any]] = None) -> Any:
        return input_data
