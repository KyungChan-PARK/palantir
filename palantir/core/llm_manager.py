import logging
from typing import Optional

from openai import OpenAI

from .config import settings

logger = logging.getLogger(__name__)


class LLMManager:
    def __init__(self, api_key: Optional[str] = None, offline: Optional[bool] = None):
        if offline is not None:
            self.offline = offline
        else:
            self.offline = getattr(settings, "OFFLINE_MODE", False)
        self.provider = getattr(settings, "LLM_PROVIDER", "openai").lower()

        if self.provider == "openai":
            # OpenAI 공식 SDK 사용
            self.client = OpenAI(api_key=api_key)
        elif self.provider in {"local", "local_mock"}:
            # 로컬 실행용 더미 클라이언트
            self.client = None
        elif self.provider == "azure":
            try:
                from openai import AzureOpenAI  # type: ignore

                self.client = AzureOpenAI(api_key=api_key)
            except Exception as e:
                logger.warning("AzureOpenAI SDK 초기화 실패: %s", e)
                self.client = None
        else:
            logger.warning(
                "지원하지 않는 LLM_PROVIDER '%s' — mock 모드로 전환", self.provider
            )
            self.client = None

    def _mock_generate(self, query: str, mode: str) -> str:
        if mode == "sql":
            return f"SELECT * FROM table WHERE text LIKE '%{query}%';"
        elif mode == "pyspark":
            return f"df.filter(df.text.contains('{query}'))"
        else:
            raise ValueError("지원하지 않는 모드입니다.")

    def generate_code(self, query: str, mode: str = "sql"):
        """LLM을 호출하거나 오프라인/모의 출력을 반환."""
        # 오프라인 모드이거나 클라이언트가 준비되지 않았으면 mock 반환
        if self.offline or self.client is None:
            logger.info("[LLMManager] 오프라인/모의 모드 — provider=%s", self.provider)
            return self._mock_generate(query, mode)

        if self.provider == "openai":
            # TODO: 실제 OpenAI function_call 파라미터 & 모델 지정
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # 예시 모델명 (환경변수화 권장)
                    messages=[{"role": "user", "content": query}],
                    temperature=0,
                )
                # 단순 예시: 전체 응답 텍스트 사용
                return response.choices[0].message.content  # type: ignore[attr-defined]
            except Exception as e:
                logger.warning("OpenAI 호출 실패 — mock 사용: %s", e)
                return self._mock_generate(query, mode)
        elif self.provider == "azure":
            # Azure OpenAI endpoint 호출 예시 — 실제 deployment_name 필요
            try:
                response = self.client.chat.completions.create(
                    deployment_name="gpt-35-turbo",  # 예시 이름
                    messages=[{"role": "user", "content": query}],
                )
                return response.choices[0].message.content  # type: ignore[attr-defined]
            except Exception as e:
                logger.warning("Azure 호출 실패 — mock 사용: %s", e)
                return self._mock_generate(query, mode)
        else:
            # 그외 provider는 아직 미구현 — mock
            return self._mock_generate(query, mode)
