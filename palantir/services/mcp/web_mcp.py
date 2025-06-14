import requests
from typing import Optional

class WebMCP:
    """웹 검색/요약을 안전하게 추상화하는 MCP 계층"""
    def __init__(self, search_api_url: Optional[str] = None):
        self.search_api_url = search_api_url or "https://api.duckduckgo.com/"
        self.max_query_length = 256

    def search(self, query: str) -> str:
        if len(query) > self.max_query_length:
            print(f"[WebMCP 오류] 쿼리 길이 초과: {len(query)}")
            return "[WebMCP 오류] 쿼리 길이 초과"
        try:
            params = {"q": query, "format": "json"}
            resp = requests.get(self.search_api_url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                print(f"[WebMCP] 검색 성공: {query}")
                return data.get("AbstractText") or str(data)
            print(f"[WebMCP 오류] 검색 실패: {resp.status_code}")
            return f"검색 실패: {resp.status_code}"
        except Exception as e:
            print(f"[WebMCP 예외] {e}")
            return f"[WebMCP 오류] {e}" 