import os
from typing import Optional, Dict, Any
import openai
from openai import AzureOpenAI
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
            self.client = openai.OpenAI(
                api_key=os.getenv("OPENAI_API_KEY")
            )
        elif settings.LLM_PROVIDER == "azure":
            self.client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
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
                    {"role": "system", "content": f"당신은 {mode} 코드 생성 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
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
                    {"role": "system", "content": "당신은 전문적인 텍스트 생성 도우미입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"텍스트 생성 실패: {str(e)}")
