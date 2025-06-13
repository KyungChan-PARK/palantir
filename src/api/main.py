from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import logging
from pydantic import BaseModel
import os
import psutil

from src.core.mcp import MCP, MCPConfig
from src.agents.base_agent import AgentConfig
from src.core.orchestrator import Orchestrator

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="AI Agent API",
    description="AI 에이전트 관리 및 실행을 위한 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 키 인증
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)

class CommandRequest(BaseModel):
    """명령어 실행 요청 모델"""
    command: str
    parameters: Dict[str, Any] = {}

class AgentRegistration(BaseModel):
    """에이전트 등록 요청 모델"""
    config: AgentConfig

class OrchestrateRequest(BaseModel):
    user_input: Any

class SelfImproveRequest(BaseModel):
    user_input: Any = None

class SelfImprovePreviewRequest(BaseModel):
    user_input: Any = None

class SelfImproveApplyRequest(BaseModel):
    suggestions: Dict[str, Any]
    approved_files: list

class SelfImproveRollbackRequest(BaseModel):
    file: str
    timestamp: str

async def verify_api_key(api_key: str = Security(api_key_header)):
    """API 키 검증"""
    if api_key != app.state.api_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    return api_key

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    # 환경 변수에서 설정 로드
    api_key = os.environ.get("MCP_API_KEY")
    if not api_key:
        logger.error("환경변수 MCP_API_KEY가 설정되어 있지 않습니다. 서버를 종료합니다.")
        import sys
        sys.exit(1)
    app.state.api_key = api_key
    app.state.base_url = os.environ.get("MCP_BASE_URL", "http://localhost:8000")

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/status")
async def get_status(api_key: str = Depends(verify_api_key)):
    """서버 상태 직접 반환"""
    return {
        "active_agents": 3,  # 실제 값으로 대체 필요
        "system_load": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent
    }

@app.post("/execute")
async def execute_command(
    request: CommandRequest,
    api_key: str = Depends(verify_api_key)
):
    """명령어 실행"""
    config = MCPConfig(
        api_key=app.state.api_key,
        base_url=app.state.base_url
    )
    async with MCP(config) as mcp:
        try:
            result = await mcp.execute_command(
                request.command,
                **request.parameters
            )
            return result
        except Exception as e:
            logger.error(f"명령어 실행 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents")
async def register_agent(
    registration: AgentRegistration,
    api_key: str = Depends(verify_api_key)
):
    """에이전트 등록"""
    config = MCPConfig(
        api_key=app.state.api_key,
        base_url=app.state.base_url
    )
    async with MCP(config) as mcp:
        try:
            result = await mcp.register_agent(registration.config.dict())
            return result
        except Exception as e:
            logger.error(f"에이전트 등록 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
async def list_agents(api_key: str = Depends(verify_api_key)):
    """샘플 에이전트 목록 직접 반환"""
    return [
        {"name": "Planner", "description": "Task Planner", "model": "gpt-4"},
        {"name": "Developer", "description": "코드 생성", "model": "gpt-4"},
        {"name": "Reviewer", "description": "코드 검토", "model": "gpt-4"}
    ]

@app.post("/orchestrate")
async def orchestrate(
    request: OrchestrateRequest,
    api_key: str = Depends(verify_api_key)
):
    """멀티에이전트 오케스트레이션 실행"""
    # 샘플 에이전트 설정 (실제 환경에서는 동적으로 관리)
    planner_cfg = AgentConfig(
        name="Planner", description="Task Planner", model="gpt-4", system_prompt="계획 수립"
    )
    dev_cfg = AgentConfig(
        name="Developer", description="코드 생성", model="gpt-4", system_prompt="코드 생성"
    )
    rev_cfg = AgentConfig(
        name="Reviewer", description="코드 검토", model="gpt-4", system_prompt="코드 검토"
    )
    orchestrator = Orchestrator(planner_cfg, dev_cfg, rev_cfg)
    try:
        result = await orchestrator.run(request.user_input)
        return result
    except Exception as e:
        logger.error(f"오케스트레이션 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/self_improve")
async def self_improve(
    request: SelfImproveRequest,
    api_key: str = Depends(verify_api_key)
):
    """자가 개선 루프 실행"""
    planner_cfg = AgentConfig(
        name="Planner", description="Task Planner", model="gpt-4", system_prompt="계획 수립"
    )
    dev_cfg = AgentConfig(
        name="Developer", description="코드 생성", model="gpt-4", system_prompt="코드 생성"
    )
    rev_cfg = AgentConfig(
        name="Reviewer", description="코드 검토", model="gpt-4", system_prompt="코드 검토"
    )
    selfimp_cfg = AgentConfig(
        name="SelfImprover", description="자가 개선", model="gpt-4", system_prompt="자가 개선"
    )
    orchestrator = Orchestrator(planner_cfg, dev_cfg, rev_cfg, selfimp_cfg)
    try:
        result = await orchestrator.run_self_improvement(request.user_input)
        return result
    except Exception as e:
        logger.error(f"자가 개선 루프 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/self_improve/preview")
async def self_improve_preview(
    request: SelfImprovePreviewRequest,
    api_key: str = Depends(verify_api_key)
):
    """자가 개선 diff/patch 목록 프리뷰"""
    planner_cfg = AgentConfig(
        name="Planner", description="Task Planner", model="gpt-4", system_prompt="계획 수립"
    )
    dev_cfg = AgentConfig(
        name="Developer", description="코드 생성", model="gpt-4", system_prompt="코드 생성"
    )
    rev_cfg = AgentConfig(
        name="Reviewer", description="코드 검토", model="gpt-4", system_prompt="코드 검토"
    )
    selfimp_cfg = AgentConfig(
        name="SelfImprover", description="자가 개선", model="gpt-4", system_prompt="자가 개선"
    )
    orchestrator = Orchestrator(planner_cfg, dev_cfg, rev_cfg, selfimp_cfg)
    agent = orchestrator.self_improver
    analysis = await agent.analyze_codebase()
    suggestions = await agent.generate_improvement_suggestions(analysis)
    preview = await agent.preview_improvements(suggestions)
    return preview

@app.post("/self_improve/apply")
async def self_improve_apply(
    request: SelfImproveApplyRequest,
    api_key: str = Depends(verify_api_key)
):
    """승인된 개선안만 실제 적용"""
    planner_cfg = AgentConfig(
        name="Planner", description="Task Planner", model="gpt-4", system_prompt="계획 수립"
    )
    dev_cfg = AgentConfig(
        name="Developer", description="코드 생성", model="gpt-4", system_prompt="코드 생성"
    )
    rev_cfg = AgentConfig(
        name="Reviewer", description="코드 검토", model="gpt-4", system_prompt="코드 검토"
    )
    selfimp_cfg = AgentConfig(
        name="SelfImprover", description="자가 개선", model="gpt-4", system_prompt="자가 개선"
    )
    orchestrator = Orchestrator(planner_cfg, dev_cfg, rev_cfg, selfimp_cfg)
    agent = orchestrator.self_improver
    result = await agent.apply_improvements(request.suggestions, request.approved_files)
    return result

@app.post("/self_improve/rollback")
async def self_improve_rollback(
    request: SelfImproveRollbackRequest,
    api_key: str = Depends(verify_api_key)
):
    """지정 파일/시점으로 롤백"""
    planner_cfg = AgentConfig(
        name="Planner", description="Task Planner", model="gpt-4", system_prompt="계획 수립"
    )
    dev_cfg = AgentConfig(
        name="Developer", description="코드 생성", model="gpt-4", system_prompt="코드 생성"
    )
    rev_cfg = AgentConfig(
        name="Reviewer", description="코드 검토", model="gpt-4", system_prompt="코드 검토"
    )
    selfimp_cfg = AgentConfig(
        name="SelfImprover", description="자가 개선", model="gpt-4", system_prompt="자가 개선"
    )
    orchestrator = Orchestrator(planner_cfg, dev_cfg, rev_cfg, selfimp_cfg)
    agent = orchestrator.self_improver
    result = await agent.rollback_improvement(request.file, request.timestamp)
    return result 