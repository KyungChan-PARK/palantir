"""상태 관리 모델"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ImprovementHistory(BaseModel):
    """개선 이력 모델"""
    timestamp: datetime = Field(default_factory=datetime.now)
    component: str = Field(description="개선된 컴포넌트")
    change_type: str = Field(description="변경 유형")
    description: str = Field(description="변경 내용")
    metrics_before: Dict = Field(description="변경 전 성능 지표")
    metrics_after: Dict = Field(description="변경 후 성능 지표")
    success: bool = Field(description="성공 여부")
    error: Optional[str] = None
    review_comments: Optional[str] = None


class PerformanceMetrics(BaseModel):
    """성능 지표 모델"""
    response_time: float = Field(default=0.0, description="응답 시간(초)")
    accuracy: float = Field(default=1.0, description="정확도(0-1)")
    memory_usage: float = Field(default=0.0, description="메모리 사용량(MB)")
    error_rate: float = Field(default=0.0, description="에러율(0-1)")
    test_coverage: float = Field(default=1.0, description="테스트 커버리지(0-1)")


class ImprovementSuggestion(BaseModel):
    """개선 제안 모델"""
    target: str = Field(description="개선 대상(code/model/test)")
    component: str = Field(description="개선할 컴포넌트")
    current_state: str = Field(description="현재 상태")
    suggested_change: str = Field(description="제안된 변경사항")
    reason: str = Field(description="개선 이유")
    priority: int = Field(description="우선순위(1-5)")
    estimated_impact: Dict[str, float] = Field(description="예상 개선 효과")


class ImprovementResult(BaseModel):
    """개선 결과 모델"""
    improvement: Dict = Field(description="적용된 개선 사항")
    fail_loop: int = Field(default=0, description="실패 횟수")
    review: Optional[str] = Field(default=None, description="리뷰 코멘트")
    test_results: Optional[List[Dict]] = Field(default=None, description="테스트 결과") 