import os
from typing import Any, Dict, Tuple

import yaml

CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../config/rss_feeds.yaml")
)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

INDICATORS = config["indicators"]
RULES = config["recommendation_rules"]


def recommend_by_rules(metrics: Dict[str, float]) -> Tuple[str, str]:
    """
    지표값(metrics)에 따라 매수/보류/매도 추천 및 근거 메시지 반환
    """
    per = metrics.get("PER")
    roe = metrics.get("ROE")
    de = metrics.get("D/E")
    # buy 조건
    if per is not None and roe is not None and de is not None:
        if per < 15 and roe > 10 and de < 1:
            return "매수", "PER 15 미만, ROE 10 초과, D/E 1 미만: 저평가 우량주"
        elif per > 30 or roe < 5:
            return "매도", "PER 30 초과 또는 ROE 5 미만: 고평가/실적 부진"
        else:
            return "보류", "지표가 중간값, 추가 뉴스/이벤트 참고 필요"
    return "보류", "지표 정보 부족"


# 테스트용 main
if __name__ == "__main__":
    sample_metrics = {"PER": 12.5, "ROE": 13.2, "D/E": 0.8}
    rec, reason = recommend_by_rules(sample_metrics)
    print(f"추천: {rec} | 근거: {reason}")
