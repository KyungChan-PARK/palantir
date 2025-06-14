import yfinance as yf
from typing import Dict, Optional

def fetch_metrics_by_ticker(ticker: str) -> Dict[str, Optional[float]]:
    """
    Yahoo Finance에서 PER, ROE, D/E 등 주요 지표를 가져온다.
    """
    info = yf.Ticker(ticker).info
    per = info.get('trailingPE')
    roe = info.get('returnOnEquity')
    de = info.get('debtToEquity')
    # ROE는 소수(0.15)로 나오는 경우가 많으니 %로 변환
    if roe is not None and roe < 1:
        roe = roe * 100
    return {'PER': per, 'ROE': roe, 'D/E': de}

# 테스트용 main
if __name__ == '__main__':
    print(fetch_metrics_by_ticker('AAPL')) 