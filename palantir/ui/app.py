"""Main dashboard application using Streamlit."""

import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from palantir.ingest.feed_manager import fetch_and_parse_feeds, filter_news_by_ticker
from palantir.ingest.metrics_fetcher import fetch_metrics_by_ticker
from palantir.analysis.analyzer import recommend_by_rules
from palantir.analysis.recommender import recommend_with_news
import yfinance as yf
from datetime import datetime, timedelta
import re
import plotly.graph_objs as go
import csv
import os

from .pages import (
    chat,
    data_explorer,
    insights,
    ontology_viewer,
    settings
)

# 피드백 로그 파일 경로
FEEDBACK_LOG = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs/feedback_log.csv'))
os.makedirs(os.path.dirname(FEEDBACK_LOG), exist_ok=True)

def log_feedback(feedback_type, content, extra=None):
    with open(FEEDBACK_LOG, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), feedback_type, content, extra])

def initialize_session_state():
    """Initialize session state variables."""
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    if "current_object" not in st.session_state:
        st.session_state.current_object = None
    
    if "selected_relationship" not in st.session_state:
        st.session_state.selected_relationship = None


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="기업 뉴스/지표 분석 대시보드",
        layout="wide"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Custom CSS
    st.markdown("""
        <style>
        .main {
            background-color: #f5f5f5;
        }
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .stSidebar {
            background-color: #ffffff;
            padding: 2rem 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.image("assets/logo.png", width=200)
        st.markdown("## Palantir AIP")
        
        selected = option_menu(
            menu_title=None,
            options=[
                "Chat Assistant",
                "Data Explorer",
                "Ontology Viewer",
                "Insights",
                "Settings"
            ],
            icons=[
                "chat-dots",
                "search",
                "diagram-3",
                "graph-up",
                "gear"
            ],
            default_index=0
        )
    
    # Main content
    if selected == "Chat Assistant":
        chat.render_page()
    
    elif selected == "Data Explorer":
        data_explorer.render_page()
    
    elif selected == "Ontology Viewer":
        ontology_viewer.render_page()
    
    elif selected == "Insights":
        insights.render_page()
    
    elif selected == "Settings":
        settings.render_page()

    # 1. 종목 티커 입력 및 리셋 버튼
    st.sidebar.header("분석할 종목 입력")
    ticker = st.sidebar.text_input("티커 (예: AAPL)", value="AAPL")
    if st.sidebar.button("차트/뉴스 선택 리셋"):
        st.session_state['selected_month'] = None
        st.session_state['highlight_date'] = None

    # 2. 실시간 지표 데이터 fetch
    metrics = fetch_metrics_by_ticker(ticker)

    # 2-1. 최근 1년치 PER, ROE, D/E 추이 시계열 데이터 (yfinance)
    def fetch_metric_history_multi(ticker: str):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y", interval="1mo")
            # PER 계산: Close / EPS (EPS는 최근 연간값 사용)
            eps = None
            try:
                income = stock.get_income_stmt()
                shares = stock.get_income_stmt().loc['Basic Shares Outstanding', :].values[0]
                net_income = stock.get_income_stmt().loc['Net Income', :].values[0]
                eps = net_income / shares if shares else None
            except Exception:
                eps = None
            if 'Close' in hist.columns and eps:
                hist['PER'] = hist['Close'] / eps
            else:
                hist['PER'] = None
            # ROE, D/E는 yfinance에서 시계열로 제공되지 않으므로 None 처리
            hist['ROE'] = None
            hist['D/E'] = None
            return hist[['PER', 'ROE', 'D/E']]
        except Exception as e:
            return None

    metric_hist = fetch_metric_history_multi(ticker)

    # 3. 뉴스 수집/필터
    try:
        feeds_data = fetch_and_parse_feeds()
        news_by_category = filter_news_by_ticker(feeds_data, ticker)
    except Exception as e:
        news_by_category = {}
        st.error(f"뉴스 데이터 수집 중 오류 발생: {e}")

    # 4. 추천 및 근거
    try:
        rec, reason = recommend_with_news(metrics, news_by_category)
    except Exception as e:
        rec, reason = "분석불가", f"추천 분석 중 오류: {e}"

    # 감성 태깅 룰(간단 버전)
    POSITIVE_WORDS = ["상승", "호재", "강세", "증가", "개선", "성장", "신기록", "최고", "수주", "돌파", "확대", "호실적", "배당", "자사주", "가이던스 상향", "목표가 상향", "Buy", "Outperform", "Positive"]
    NEGATIVE_WORDS = ["하락", "악재", "약세", "감소", "부진", "적자", "실적악화", "최저", "경고", "축소", "실패", "감자", "부채", "가이던스 하향", "목표가 하향", "Sell", "Underperform", "Negative"]
    def get_sentiment(text):
        for w in POSITIVE_WORDS:
            if w.lower() in text.lower():
                return "🟢 긍정"
        for w in NEGATIVE_WORDS:
            if w.lower() in text.lower():
                return "🔴 부정"
        return "⚪️ 중립"

    # 5. 탭 UI로 시각화
    TABS = ["지표/차트", "뉴스", "추천"]
    tab1, tab2, tab3 = st.tabs(TABS)

    # 차트-뉴스 연동: 클릭된 월(데이터 포인트) 상태 저장
    if 'selected_month' not in st.session_state:
        st.session_state['selected_month'] = None
    # 뉴스→차트 연동: 클릭된 뉴스 날짜 상태 저장
    if 'highlight_date' not in st.session_state:
        st.session_state['highlight_date'] = None

    with tab1:
        st.subheader(f"[{ticker}] 핵심 재무 지표")
        if not metrics or all(v is None for v in metrics.values()):
            st.warning("지표 데이터를 불러올 수 없습니다. (티커 확인 또는 데이터 소스 점검 필요)")
        else:
            metrics_df = pd.DataFrame([metrics], index=[ticker])
            st.table(metrics_df)
        st.subheader("지표 추이(최근 1년)")
        if metric_hist is not None and not metric_hist.empty:
            chart_data = metric_hist.copy()
            chart_data = chart_data.dropna(axis=1, how='all')
            if chart_data.shape[1] > 0 and chart_data.notnull().any().any():
                fig = go.Figure()
                if 'PER' in chart_data.columns:
                    fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['PER'], mode='lines+markers', name='PER'))
                # 뉴스→차트 연동: 마커 표시
                if st.session_state['highlight_date']:
                    highlight_x = pd.to_datetime(st.session_state['highlight_date'])
                    if highlight_x in chart_data.index:
                        fig.add_trace(go.Scatter(x=[highlight_x], y=[chart_data.loc[highlight_x, 'PER']],
                                                 mode='markers', marker=dict(size=16, color='red', symbol='star'),
                                                 name='뉴스 선택'))
                fig.update_layout(clickmode='event+select', xaxis_title='날짜', yaxis_title='PER')
                selected = st.plotly_chart(fig, use_container_width=True)
                months = [d.strftime('%Y-%m') for d in chart_data.index]
                month_select = st.selectbox('특정 월의 뉴스만 보기', ['전체'] + months, index=0)
                if month_select != '전체':
                    st.session_state['selected_month'] = month_select
                else:
                    st.session_state['selected_month'] = None
            else:
                st.info("PER, ROE, D/E 시계열 데이터를 불러올 수 없습니다.")
        else:
            st.info("PER, ROE, D/E 시계열 데이터를 불러올 수 없습니다.")

    with tab2:
        st.subheader(f"[{ticker}] 카테고리별 최신 뉴스")
        all_news = [(cat, entry) for cat, entries in news_by_category.items() for entry in entries]
        keyword = st.text_input("뉴스 키워드 필터", value="")
        days = st.slider("최근 N일 이내 뉴스만 보기", min_value=1, max_value=90, value=30)
        cutoff = datetime.now() - timedelta(days=days)
        sentiment_options = ["전체", "🟢 긍정", "🔴 부정", "⚪️ 중립"]
        sentiment_filter = st.selectbox("감성(긍정/부정/중립) 필터", sentiment_options, index=0)
        st.markdown("**카테고리별 뉴스 개수**")
        cat_counts = {cat: len(entries) for cat, entries in news_by_category.items()}
        st.write({k: v for k, v in cat_counts.items() if v > 0})
        if not news_by_category or all(len(v) == 0 for v in news_by_category.values()):
            st.info("관련 뉴스를 찾을 수 없습니다.")
        else:
            for category, entries in news_by_category.items():
                filtered = []
                for idx, entry in enumerate(entries):
                    title = getattr(entry, 'title', '')
                    summary = getattr(entry, 'summary', '')
                    published = getattr(entry, 'published', '')
                    url = getattr(entry, 'link', '')
                    pub_dt = None
                    try:
                        pub_dt = datetime.strptime(published[:19], "%Y-%m-%dT%H:%M:%S") if published else None
                    except Exception:
                        pub_dt = None
                    if keyword and keyword.lower() not in title.lower() and keyword.lower() not in summary.lower():
                        continue
                    if pub_dt and pub_dt < cutoff:
                        continue
                    sentiment = get_sentiment(title + ' ' + summary)
                    if sentiment_filter != "전체" and sentiment != sentiment_filter:
                        continue
                    if st.session_state['selected_month']:
                        if not pub_dt or pub_dt.strftime('%Y-%m') != st.session_state['selected_month']:
                            continue
                    filtered.append((title, summary, url, published, sentiment, pub_dt))
                if not filtered:
                    continue
                st.markdown(f"**{category}** <span style='background-color:#eee;border-radius:8px;padding:2px 8px;'>{len(filtered)}</span>", unsafe_allow_html=True)
                for i, (title, summary, url, published, sentiment, pub_dt) in enumerate(filtered):
                    def highlight(text, kw):
                        if not kw:
                            return text
                        pattern = re.compile(re.escape(kw), re.IGNORECASE)
                        return pattern.sub(f"<mark style='background: #ffe066'>{kw}</mark>", text)
                    title_html = highlight(title, keyword)
                    # 뉴스 클릭 시 해당 날짜 차트에 마커 표시
                    btn_key = f"newsbtn_{category}_{i}"
                    if st.button(f"뉴스 날짜 차트에 표시: {title[:30]}...", key=btn_key):
                        if pub_dt:
                            st.session_state['highlight_date'] = pub_dt.strftime('%Y-%m-%d')
                    st.markdown(f"- <a href='{url}' target='_blank'>{title_html}</a> <span style='font-size:0.9em'>{sentiment}</span>", unsafe_allow_html=True)
                    if summary:
                        st.caption(highlight(summary, keyword), unsafe_allow_html=True)
                    if published:
                        st.caption(f"🕒 {published}")
                    # 뉴스 피드백 버튼
                    col_like, col_dislike = st.columns([1,1])
                    with col_like:
                        if st.button(f"👍 좋아요_{category}_{i}"):
                            log_feedback('news_like', title, url)
                            st.success("피드백(좋아요) 기록됨")
                    with col_dislike:
                        if st.button(f"👎 싫어요_{category}_{i}"):
                            log_feedback('news_dislike', title, url)
                            st.info("피드백(싫어요) 기록됨")

    with tab3:
        st.subheader("투자 추천 의견")
        if rec == "매수":
            st.success(f"매수: {reason}")
        elif rec == "매도":
            st.error(f"매도: {reason}")
        elif rec == "보류":
            st.info(f"보류: {reason}")
        else:
            st.warning(f"추천 불가: {reason}")
        col_acc, col_inacc = st.columns([1,1])
        with col_acc:
            if st.button("✅ 추천 정확(맞음)"):
                log_feedback('recommendation_correct', rec, reason)
                st.success("추천 정확 피드백 기록됨")
        with col_inacc:
            if st.button("❌ 추천 부정확(틀림)"):
                log_feedback('recommendation_incorrect', rec, reason)
                st.info("추천 부정확 피드백 기록됨")


if __name__ == "__main__":
    main() 