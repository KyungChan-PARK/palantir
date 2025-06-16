import os
from typing import Dict, List

import feedparser
import requests
import yaml

CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../config/rss_feeds.yaml")
)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

FEED_URLS = config["feeds"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # 필요시 쿠키 등 추가
}

# ETag/Last-Modified 캐시 (메모리, 필요시 파일로 영속화)
etag_cache = {cat: None for cat in FEED_URLS}
modified_cache = {cat: None for cat in FEED_URLS}


def fetch_and_parse_feeds() -> Dict[str, List[dict]]:
    """카테고리별 RSS 피드 파싱 결과 반환"""
    feeds_data = {}
    for category, url in FEED_URLS.items():
        # feedparser의 조건부 요청 지원
        result = feedparser.parse(
            url,
            etag=etag_cache[category],
            modified=modified_cache[category],
            request_headers=HEADERS,
        )
        if getattr(result, "status", 200) == 304:
            feeds_data[category] = []  # 업데이트 없음
        else:
            etag_cache[category] = getattr(result, "etag", None)
            modified_cache[category] = getattr(result, "modified", None)
            feeds_data[category] = result.entries
    return feeds_data


def filter_news_by_ticker(
    feeds_data: Dict[str, List[dict]], ticker: str
) -> Dict[str, List[dict]]:
    """카테고리별로 티커가 언급된 뉴스만 필터링"""
    news_by_category = {cat: [] for cat in FEED_URLS}
    for category, entries in feeds_data.items():
        for entry in entries:
            title = getattr(entry, "title", "")
            summary = getattr(entry, "summary", "")
            # 괄호 포함, 대소문자 무시, 회사명 등 추가 가능
            if (
                ticker.upper() in title.upper()
                or ticker.upper() in summary.upper()
                or f"({ticker.upper()})" in title.upper()
            ):
                news_by_category[category].append(entry)
    return news_by_category


# 테스트용 메인
if __name__ == "__main__":
    feeds_data = fetch_and_parse_feeds()
    ticker = "AAPL"  # 예시
    news = filter_news_by_ticker(feeds_data, ticker)
    for cat, items in news.items():
        print(f"[{cat}] {len(items)}건")
