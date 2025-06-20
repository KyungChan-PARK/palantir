import os
from typing import List, Dict, Any, Optional
import openai
import anthropic
from tenacity import retry, wait_random_exponential, stop_after_attempt

# 환경 변수에서 API 키 로드
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(3))
def call_llm(messages: List[Dict[str, str]], max_tokens: int = 2048) -> str:
    """
    LLM API를 호출하는 통합 함수
    
    Args:
        messages: 대화 메시지 목록
        max_tokens: 최대 토큰 수
        
    Returns:
        str: LLM의 응답 텍스트
    """
    try:
        if MODEL.startswith("gpt"):
            response = openai.ChatCompletion.create(
                model=MODEL,
                messages=messages,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        else:
            client = anthropic.Client(os.getenv("ANTHROPIC_API_KEY"))
            response = client.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                messages=messages
            )
            return response.content[0].text.strip()
    except Exception as e:
        print(f"LLM API 호출 중 오류 발생: {str(e)}")
        raise

def create_system_message(content: str) -> Message:
    """시스템 메시지 생성"""
    return Message("system", content)

def create_user_message(content: str) -> Message:
    """사용자 메시지 생성"""
    return Message("user", content)

def create_assistant_message(content: str) -> Message:
    """어시스턴트 메시지 생성"""
    return Message("assistant", content) 