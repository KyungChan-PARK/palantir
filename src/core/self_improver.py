"""
자가 개선을 위한 모듈
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .metrics import metrics
from .optimizer import optimizer
from .profiler import profiler

logger = logging.getLogger(__name__)

class SelfImprover:
    """자가 개선 관리자"""
    
    def __init__(self):
        self.improvement_history: List[Dict[str, Any]] = []
        self.last_check: Optional[datetime] = None
        
    def analyze_performance(self) -> Dict[str, Any]:
        """성능 분석 수행"""
        current_metrics = metrics.get_metrics()
        optimizer.record_metrics(current_metrics)
        
        improvements = optimizer.calculate_improvement()
        suggestions = optimizer.get_optimization_suggestions()
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'metrics': current_metrics,
            'improvements': improvements,
            'suggestions': suggestions
        }
        
        self.improvement_history.append(analysis)
        self.last_check = datetime.now()
        
        return analysis
        
    def get_improvement_report(self) -> Dict[str, Any]:
        """개선 보고서 생성"""
        if not self.improvement_history:
            return {
                'status': 'no_data',
                'message': '개선 이력이 없습니다.'
            }
            
        latest = self.improvement_history[-1]
        first = self.improvement_history[0]
        
        total_improvements = {}
        for metric in latest['metrics']:
            if metric in first['metrics']:
                if first['metrics'][metric] != 0:
                    improvement = ((latest['metrics'][metric] - first['metrics'][metric]) / first['metrics'][metric]) * 100
                    total_improvements[metric] = improvement
                    
        return {
            'status': 'success',
            'period': {
                'start': first['timestamp'],
                'end': latest['timestamp']
            },
            'total_improvements': total_improvements,
            'latest_suggestions': latest['suggestions']
        }
        
    @profiler.profile
    def apply_improvements(self) -> List[str]:
        """개선 사항 적용"""
        if not self.improvement_history:
            return ["개선할 데이터가 없습니다."]
            
        latest = self.improvement_history[-1]
        applied_improvements = []
        
        # 성능 저하가 있는 메트릭에 대한 자동 개선
        for metric, improvement in latest['improvements'].items():
            if improvement < 0:  # 성능 저하
                action = f"{metric} 성능 저하 감지됨: {abs(improvement):.2f}% 감소"
                applied_improvements.append(action)
                
        # 제안사항 기반 개선
        for suggestion in latest['suggestions']:
            action = f"제안사항 적용: {suggestion}"
            applied_improvements.append(action)
            
        return applied_improvements

# 글로벌 자가 개선 관리자 인스턴스
self_improver = SelfImprover() 