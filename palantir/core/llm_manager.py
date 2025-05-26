from openai import OpenAI

class LLMManager:
    def __init__(self, api_key=None):
        self.client = OpenAI(api_key=api_key)

    def generate_code(self, query: str, mode: str = "sql"):
        # 실제 function_call 예시는 아래와 같이 작성
        # 실제 배포 시에는 OpenAI function_call 파라미터를 맞춰야 함
        # 여기서는 mock response
        if mode == "sql":
            return f"SELECT * FROM table WHERE text LIKE '%{query}%';"
        elif mode == "pyspark":
            return f"df.filter(df.text.contains('{query}'))"
        else:
            raise ValueError("지원하지 않는 모드입니다.") 