import streamlit as st
import pandas as pd
import os
import csv
from collections import Counter

st.set_page_config(page_title="피드백 분석 대시보드", layout="wide")
st.title("피드백 분석 대시보드 (뉴스/추천)")

FEEDBACK_LOG = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs/feedback_log.csv'))

if not os.path.exists(FEEDBACK_LOG):
    st.warning("피드백 로그 파일이 존재하지 않습니다.")
    st.stop()

# 1. 피드백 로그 로드
cols = ['timestamp', 'type', 'content', 'extra']
with open(FEEDBACK_LOG, encoding='utf-8') as f:
    reader = csv.reader(f)
    data = list(reader)

df = pd.DataFrame(data, columns=cols)

# 2. 피드백 유형별 통계
st.subheader("전체 피드백 분포")
count_by_type = df['type'].value_counts()
st.bar_chart(count_by_type)

# 3. 뉴스 피드백(좋아요/싫어요) 통계
st.subheader("뉴스별 좋아요/싫어요 TOP 10")
news_likes = df[df['type'] == 'news_like']['content'].value_counts().head(10)
news_dislikes = df[df['type'] == 'news_dislike']['content'].value_counts().head(10)
st.write("**좋아요 TOP 10**")
st.table(news_likes)
st.write("**싫어요 TOP 10**")
st.table(news_dislikes)

# 4. 추천 피드백(정확/부정확) 통계
st.subheader("추천 결과 피드백 통계")
rec_acc = df[df['type'] == 'recommendation_correct']['content'].value_counts()
rec_inacc = df[df['type'] == 'recommendation_incorrect']['content'].value_counts()
st.write("**정확(맞음) 추천 결과**")
st.table(rec_acc)
st.write("**부정확(틀림) 추천 결과**")
st.table(rec_inacc)

# 5. 개선 제안(간단 룰)
st.subheader("개선 제안 (임시)")
# 좋아요/싫어요가 많은 뉴스 키워드, 추천 정확/부정확 비율 높은 추천 유형 등
if not news_dislikes.empty:
    st.info(f"싫어요가 많은 뉴스 키워드(상위 3): {', '.join(news_dislikes.index[:3])}")
if not rec_inacc.empty:
    st.info(f"부정확 피드백이 많은 추천 결과(상위 3): {', '.join(rec_inacc.index[:3])}")

st.caption("※ 이 대시보드는 logs/feedback_log.csv의 피드백을 기반으로 실시간 통계/개선 제안을 제공합니다. 룰/임계치/키워드 자동 보정은 추후 ML/LLM 연동으로 확장 가능합니다.") 