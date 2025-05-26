from openai import OpenAI
from .config import settings
import logging

logger = logging.getLogger(__name__)

class LLMManager:
    def __init__(self, api_key=None):
        self.client = OpenAI(api_key=api_key)

    def generate_code(self, query: str, mode: str = "sql"):
        # 실제 function_call 예시는 아래와 같이 작성
        # 실제 배포 시에는 OpenAI function_call 파라미터를 맞춰야 함
        # 여기서는 mock response
        if getattr(settings, "OFFLINE_MODE", False) and getattr(settings, "LLM_PROVIDER", "openai").lower() == "openai":
            logger.warning("OpenAI API 호출이 오프라인 모드에서 건너뛰어졌습니다.")
            return "OpenAI 기능은 오프라인 모드에서 비활성화되었습니다." # 또는 적절한 모의 응답/예외 처리
        if mode == "sql":
            return f"SELECT * FROM table WHERE text LIKE '%{query}%';"
        elif mode == "pyspark":
            return f"df.filter(df.text.contains('{query}'))"
        else:
            raise ValueError("지원하지 않는 모드입니다.") 