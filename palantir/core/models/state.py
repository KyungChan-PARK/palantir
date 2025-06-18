"""상태 관리 모델"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ImprovementHistory(BaseModel):
    """개선 이력 모델"""
    timestamp: datetime = Field(default_factory=datetime.now)
    component: str
    change_type: str
    description: str
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]
    success: bool
    error: Optional[str] = None
    review_comments: Optional[str] = None


class PerformanceMetrics(BaseModel):
    """성능 지표 모델"""
    response_time: float = 0.0  # 초 단위
    accuracy: float = 0.0  # 0-1 사이 값
    memory_usage: float = 0.0  # MB 단위
    error_rate: float = 0.0  # 0-1 사이 값
    test_coverage: float = 0.0  # 0-1 사이 값


class ImprovementSuggestion(BaseModel):
    """개선 제안 모델"""
    target: str  # 'code', 'config', 'data' 등
    component: str  # 구체적인 컴포넌트 이름
    current_state: str  # 현재 상태 설명
    suggested_change: str  # 제안된 변경 사항
    reason: str  # 변경이 필요한 이유
    priority: int  # 1-5 (1이 가장 높은 우선순위)
    estimated_impact: Dict[str, float]  # 예상되는 성능 지표 변화


class ImprovementResult(BaseModel):
    """개선 결과 모델"""
    improvement: Dict  # 적용된 개선 사항
    fail_loop: int = 0  # 실패 횟수
    review: Optional[str] = None  # 리뷰 코멘트 