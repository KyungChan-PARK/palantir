import os
from typing import Any, Dict, Optional

import openai
from openai import AzureOpenAI
import anthropic
from anthropic import Anthropic

from .config import settings


class LLMManager:
    def __init__(self, offline: bool = False):
        self.offline = offline
        self.client = None
        self._init_client()

    def _init_client(self):
        """LLM 클라이언트를 초기화합니다."""
        if self.offline:
            return

        if settings.LLM_PROVIDER == "openai":
            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif settings.LLM_PROVIDER == "azure":
            self.client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            )
        elif settings.LLM_PROVIDER == "anthropic":
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        elif settings.LLM_PROVIDER == "local":
            # 로컬 모델 설정
            pass
        else:
            raise ValueError(f"지원하지 않는 LLM 제공자: {settings.LLM_PROVIDER}")

    def generate_code(self, prompt: str, mode: str = "sql") -> str:
        """프롬프트를 기반으로 코드를 생성합니다."""
        if mode not in ("sql", "pyspark"):
            raise ValueError("지원하지 않는 모드")

        if self.offline:
            return "SELECT 1" if mode == "sql" else "df.filter()"

        try:
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[
                    {
                        "role": "system",
                        "content": f"당신은 {mode} 코드 생성 전문가입니다.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"코드 생성 실패: {str(e)}")

    def generate_text(self, prompt: str) -> str:
        """프롬프트를 기반으로 텍스트를 생성합니다."""
        if self.offline:
            return "오프라인 모드에서는 텍스트 생성이 불가능합니다."

        try:
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 전문적인 텍스트 생성 도우미입니다.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"텍스트 생성 실패: {str(e)}")

    async def generate(self, prompt: str, system_message: Optional[str] = None, **kwargs) -> str:
        """프롬프트를 LLM에 전달하고 응답을 반환합니다."""
        if self.offline:
            return "[오프라인 모드] LLM 응답을 생성할 수 없습니다."

        try:
            if settings.LLM_PROVIDER == "openai":
                messages = []
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                messages.append({"role": "user", "content": prompt})
                
                response = await self.client.chat.completions.create(
                    model=kwargs.get("model", settings.DEFAULT_MODEL),
                    messages=messages,
                    temperature=kwargs.get("temperature", 0.7),
                    max_tokens=kwargs.get("max_tokens", 2000)
                )
                return response.choices[0].message.content

            elif settings.LLM_PROVIDER == "anthropic":
                message = await self.client.messages.create(
                    model=kwargs.get("model", settings.ANTHROPIC_MODEL),
                    max_tokens=kwargs.get("max_tokens", 2000),
                    temperature=kwargs.get("temperature", 0.7),
                    system=system_message if system_message else None,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text

            elif settings.LLM_PROVIDER == "local":
                # 로컬 모델 구현
                pass

        except Exception as e:
            raise Exception(f"LLM 호출 중 오류 발생: {str(e)}")

        return "[알 수 없는 LLM 제공자] 응답을 생성할 수 없습니다."
