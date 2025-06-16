import os
from typing import Optional

from ...core.exceptions import MCPError


class LLMMCP:
    """Unified interface to call various LLM providers."""

    def __init__(self, provider: str = "openai", model: Optional[str] = None):
        self.provider = provider
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.api_key = os.getenv("OPENAI_API_KEY")

    async def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs,
    ) -> str:
        if self.provider == "openai":
            try:
                import openai
            except ImportError as e:
                raise MCPError("openai 패키지가 필요합니다") from e
            try:
                messages = []
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                messages.append({"role": "user", "content": prompt})
                response = await openai.ChatCompletion.acreate(
                    model=self.model,
                    messages=messages,
                    api_key=self.api_key,
                    temperature=kwargs.get("temperature", 0.7),
                    max_tokens=kwargs.get("max_tokens", 512),
                )
                if isinstance(response, dict):
                    return response["choices"][0]["message"]["content"]
                if hasattr(response, "choices"):
                    return response.choices[0].message.content
                return str(response)
            except Exception as e:
                raise MCPError(str(e)) from e
        return "(LLM 응답 예시)"
