"""테스트용 LLM 프로바이더"""

import re
from typing import Dict, Any, Optional


def call_api(prompt: str, options: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """테스트용 LLM API 호출

    Args:
        prompt: 프롬프트 문자열
        options: LLM 설정 (temperature 등)
        context: 추가 컨텍스트

    Returns:
        Dict[str, str]: LLM 응답
    """
    # API 엔드포인트 생성 응답
    if "API 엔드포인트" in prompt:
        return {
            "output": """```python
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .database import get_db
from .models import Item
from .schemas import ItemResponse

router = APIRouter()

@router.get("/api/v1/items", response_model=List[ItemResponse])
async def get_items(
    page: int = Query(1, gt=0),
    limit: int = Query(10, gt=0, le=100),
    search_query: Optional[str] = None,
    db: Session = Depends(get_db)
):
    \"\"\"아이템 목록 조회

    Args:
        page: 페이지 번호
        limit: 페이지당 아이템 수
        search_query: 검색어
        db: 데이터베이스 세션

    Returns:
        List[ItemResponse]: 아이템 목록
    \"\"\"
    skip = (page - 1) * limit
    query = db.query(Item)
    
    if search_query:
        query = query.filter(Item.name.ilike(f"%{search_query}%"))
    
    items = query.offset(skip).limit(limit).all()
    return [ItemResponse.from_orm(item) for item in items]
```"""
        }

    # 코드 리뷰 응답
    elif "코드 리뷰" in prompt:
        return {
            "output": """개선 제안:

1. 코드 품질 및 가독성
   - 리스트 컴프리헨션 사용: `return [i * 2 for i in items if i > 0]`
   - 타입 힌트 추가: `def process_items(items: List[int]) -> List[int]:`
   - 함수 문서화: docstring 추가

2. 성능 및 확장성
   - 대용량 데이터 처리를 위한 제너레이터 고려
   - 병렬 처리 가능성 검토

3. 보안 및 안정성
   - 입력 값 검증 추가
   - 예외 처리 구현

4. 테스트 커버리지
   - 단위 테스트 작성
   - 엣지 케이스 테스트"""
        }

    # 버그 수정 응답
    elif "버그 리포트" in prompt:
        return {
            "output": """분석 및 해결 방안:

1. 근본 원인
   - 연결 풀 관리 부재
   - 재시도 로직 없음
   - 타임아웃 설정 미흡

2. 해결 방안
```python
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)
SessionLocal = sessionmaker(engine, class_=AsyncSession)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()
```

3. 재발 방지
   - 연결 상태 모니터링 추가
   - 로드 밸런싱 검토
   - 장애 복구 전략 수립"""
        }

    # 리팩토링 응답
    elif "리팩토링" in prompt:
        return {
            "output": """리팩토링 제안:

1. 현재 구조 분석
   - UserService가 너무 많은 책임을 가짐
   - 단일 책임 원칙 위반
   - 테스트와 유지보수가 어려움

2. 개선된 구조
```python
from dataclasses import dataclass
from typing import Protocol

class EmailService(Protocol):
    async def send_email(self, user: User, template: str, **kwargs): ...

class ActivityLogger(Protocol):
    async def log_activity(self, user: User, action: str): ...

@dataclass
class UserService:
    email_service: EmailService
    activity_logger: ActivityLogger
    user_repository: UserRepository

    async def create_user(self, data: UserCreate) -> User:
        user = await self.user_repository.create(data)
        await self.email_service.send_email(user, "welcome")
        await self.activity_logger.log_activity(user, "created")
        return user
```

3. 개선점
   - 의존성 주입으로 결합도 감소
   - 인터페이스 분리로 유연성 향상
   - 테스트 용이성 증가"""
        }

    # 기본 응답
    return {
        "output": f"테스트 응답: {prompt[:100]}..."
    }
