"""
성능 최적화를 위한 모듈
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.metrics import mean_squared_error

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """성능 최적화기"""
    
    def __init__(self):
        self.metrics_history: List[Dict[str, float]] = []
        self.baseline_metrics: Optional[Dict[str, float]] = None
        
    def record_metrics(self, metrics: Dict[str, float]):
        """메트릭 기록"""
        self.metrics_history.append(metrics)
        if self.baseline_metrics is None:
            self.baseline_metrics = metrics.copy()
            
    def calculate_improvement(self) -> Dict[str, float]:
        """성능 개선도 계산"""
        if not self.metrics_history or self.baseline_metrics is None:
            return {}
            
        latest_metrics = self.metrics_history[-1]
        improvements = {}
        
        for metric, value in latest_metrics.items():
            if metric in self.baseline_metrics:
                baseline = self.baseline_metrics[metric]
                if baseline != 0:
                    improvement = ((value - baseline) / baseline) * 100
                    improvements[metric] = improvement
                    
        return improvements
        
    def get_optimization_suggestions(self) -> List[str]:
        """최적화 제안사항 생성"""
        if len(self.metrics_history) < 2:
            return ["충분한 메트릭 데이터가 수집되지 않았습니다."]
            
        suggestions = []
        metrics = np.array([list(m.values()) for m in self.metrics_history])
        
        # 성능 저하 탐지
        for i, metric_name in enumerate(self.metrics_history[0].keys()):
            metric_values = metrics[:, i]
            if len(metric_values) >= 3:
                trend = np.polyfit(range(len(metric_values)), metric_values, 1)[0]
                if trend > 0:  # 값이 증가하는 추세 (성능 저하)
                    suggestions.append(f"{metric_name} 지표가 지속적으로 증가하고 있습니다. 최적화가 필요할 수 있습니다.")
                    
        return suggestions

# 글로벌 최적화기 인스턴스
optimizer = PerformanceOptimizer() 