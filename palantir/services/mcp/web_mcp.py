from typing import Optional

import aiohttp

from ...core.exceptions import MCPError


class WebMCP:
    """Simple HTTP request wrapper."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url

    async def request(self, url: str) -> dict:
        target = self.base_url + url if self.base_url else url
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(target) as resp:
                    if resp.status != 200:
                        raise MCPError("요청 실패")
                    return await resp.json()
        except Exception as e:
            raise MCPError(str(e)) from e
