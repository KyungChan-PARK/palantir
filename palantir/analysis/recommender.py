from typing import Dict, Tuple
from .analyzer import recommend_by_rules


def adjust_recommendation_by_news(
    base_rec: str, news_by_category: Dict[str, list]
) -> str:
    """
    뉴스 이벤트(배당, 자사주, 가이던스, 부채 등)로 추천 보정
    """
    positive_events = (
        news_by_category.get("Dividends")
        or news_by_category.get("Buybacks")
        or news_by_category.get("Guidance")
    )
    negative_events = news_by_category.get("Debt/Share Issuance")
    if base_rec == "보류":
        if positive_events and len(positive_events) > 0:
            return "매수"
        elif negative_events and len(negative_events) > 0:
            return "매도"
    return base_rec


def recommend_with_news(
    metrics: Dict[str, float], news_by_category: Dict[str, list]
) -> Tuple[str, str]:
    base_rec, reason = recommend_by_rules(metrics)
    final_rec = adjust_recommendation_by_news(base_rec, news_by_category)
    if final_rec != base_rec:
        if final_rec == "매수":
            reason += " | 최근 배당/자사주/가이던스 뉴스로 긍정적 신호"
        elif final_rec == "매도":
            reason += " | 최근 부채/주식발행 뉴스로 부정적 신호"
    return final_rec, reason


# 테스트용 main
if __name__ == "__main__":
    metrics = {"PER": 18.0, "ROE": 12.0, "D/E": 0.9}
    news = {"Dividends": [{}], "Debt/Share Issuance": []}
    rec, reason = recommend_with_news(metrics, news)
    print(f"최종 추천: {rec} | 근거: {reason}")
