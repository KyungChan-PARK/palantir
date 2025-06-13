import os
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
import aiohttp
import asyncio
from pydantic import BaseModel, Field

class MCPConfig(BaseModel):
    """MCP 설정을 위한 모델"""
    api_key: str = Field(..., description="API 키")
    base_url: str = Field(default="http://localhost:8000", description="API 기본 URL")
    timeout: int = Field(default=30, description="API 타임아웃(초)")
    max_retries: int = Field(default=3, description="최대 재시도 횟수")

class MCP:
    """Master Control Program API 클라이언트"""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession(
            headers={"X-API-Key": self.config.api_key},
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
    
    async def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """명령어 실행"""
        if not self.session:
            raise RuntimeError("MCP 세션이 초기화되지 않았습니다.")
        
        for attempt in range(self.config.max_retries):
            try:
                async with self.session.post(
                    f"{self.config.base_url}/execute",
                    json={"command": command, **kwargs}
                ) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                self.logger.error(f"명령어 실행 실패 (시도 {attempt + 1}/{self.config.max_retries}): {str(e)}")
                if attempt == self.config.max_retries - 1:
                    raise
    
    async def get_status(self) -> Dict[str, Any]:
        """MCP 상태 확인"""
        if not self.session:
            raise RuntimeError("MCP 세션이 초기화되지 않았습니다.")
        
        async with self.session.get(f"{self.config.base_url}/status") as response:
            response.raise_for_status()
            return await response.json()
    
    async def register_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 등록"""
        if not self.session:
            raise RuntimeError("MCP 세션이 초기화되지 않았습니다.")
        
        async with self.session.post(
            f"{self.config.base_url}/agents",
            json=agent_config
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """등록된 에이전트 목록 조회"""
        if not self.session:
            raise RuntimeError("MCP 세션이 초기화되지 않았습니다.")
        
        async with self.session.get(f"{self.config.base_url}/agents") as response:
            response.raise_for_status()
            return await response.json()

    async def llm_generate(self, prompt: str, model: str = "gpt-4o", **kwargs) -> dict:
        """LLM 모델별 프롬프트 호출 (모델명 파라미터화, 5개 모델만 허용)"""
        allowed_models = ["gpt-4o", "o3", "o3-pro", "o4-mini", "o4-mini-high"]
        if model not in allowed_models:
            raise ValueError(f"지원하지 않는 모델입니다. (허용 모델: {', '.join(allowed_models)})")
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            raise RuntimeError("OpenAI API Key(OPENAI_API_KEY 환경변수)가 설정되어 있지 않습니다. 관리자에게 문의하세요.")
        # 실제 OpenAI API 호출 예시 (비동기)
        import openai
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": kwargs.get("system_prompt", "You are an AI agent.")},
                      {"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.2),
            max_tokens=kwargs.get("max_tokens", 2048),
            response_format={"type": "json_object"}
        )
        return {"text": response.choices[0].message.content}

    async def file_op(self, op: str, path: str, content: str = None) -> dict:
        """파일 시스템 관련 작업 (예: read, write, delete)"""
        return await self.execute_command("file_op", op=op, path=path, content=content)

    async def git_op(self, op: str, repo_path: str, args: dict = None) -> dict:
        """Git 관련 작업 (예: commit, push, pull, branch 등)"""
        return await self.execute_command("git_op", op=op, repo_path=repo_path, args=args or {})

    async def test_run(self, test_type: str = "pytest", target: str = "tests/") -> dict:
        """테스트 실행 (예: pytest, unittest 등)"""
        return await self.execute_command("test_run", test_type=test_type, target=target)

    async def web_search(self, query: str, top_k: int = 3) -> dict:
        """웹 검색 (예: Bing, Google 등)"""
        return await self.execute_command("web_search", query=query, top_k=top_k) 