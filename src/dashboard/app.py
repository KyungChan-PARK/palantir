import streamlit as st
import requests
import json
from typing import Dict, Any
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os

# API 설정
API_URL = "http://localhost:8000"
API_KEY = os.environ.get("MCP_API_KEY", "palantir")  # 환경변수에서 읽고, 없으면 기본값

def get_headers() -> Dict[str, str]:
    """API 요청 헤더 생성"""
    return {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

def get_status() -> Dict[str, Any]:
    """서버 상태 조회"""
    response = requests.get(f"{API_URL}/status", headers=get_headers())
    return response.json()

def get_agents() -> list:
    """등록된 에이전트 목록 조회"""
    response = requests.get(f"{API_URL}/agents", headers=get_headers())
    return response.json()

def execute_command(command: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """명령어 실행"""
    data = {
        "command": command,
        "parameters": parameters or {}
    }
    response = requests.post(
        f"{API_URL}/execute",
        headers=get_headers(),
        json=data
    )
    return response.json()

def register_agent(config: Dict[str, Any]) -> Dict[str, Any]:
    """에이전트 등록"""
    data = {"config": config}
    response = requests.post(
        f"{API_URL}/agents",
        headers=get_headers(),
        json=data
    )
    return response.json()

# Streamlit 앱 설정
st.set_page_config(
    page_title="AI Agent Dashboard",
    page_icon="🤖",
    layout="wide"
)

# 사이드바
st.sidebar.title("AI Agent Dashboard")
st.sidebar.info("AI 에이전트 관리 및 모니터링 대시보드")

# 메인 페이지
st.title("AI Agent Dashboard")

# 상태 정보
st.header("시스템 상태")
try:
    status = get_status()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("활성 에이전트", status.get("active_agents") if status.get("active_agents") is not None else 0)
    with col2:
        sys_load = status.get("system_load")
        st.metric("시스템 부하", f"{sys_load:.1f}%" if sys_load is not None else "0.0%")
    with col3:
        mem_usage = status.get("memory_usage")
        st.metric("메모리 사용량", f"{mem_usage:.1f}%" if mem_usage is not None else "0.0%")
except Exception as e:
    st.error(f"상태 정보를 가져오는데 실패했습니다: {str(e)}")

# 에이전트 목록
st.header("등록된 에이전트")
try:
    agents = get_agents()
    if isinstance(agents, list) and len(agents) > 0 and isinstance(agents[0], dict):
        df = pd.DataFrame(agents)
        st.dataframe(df)
    elif isinstance(agents, list) and len(agents) == 0:
        st.info("등록된 에이전트가 없습니다.")
    else:
        st.error("에이전트 데이터 형식이 올바르지 않습니다: " + str(agents))
except Exception as e:
    st.error(f"에이전트 목록을 가져오는데 실패했습니다: {str(e)}")

# 명령어 실행
st.header("명령어 실행")
command = st.text_input("명령어")
parameters = st.text_area("매개변수 (JSON 형식)", "{}")

if st.button("실행"):
    try:
        params = json.loads(parameters)
        result = execute_command(command, params)
        st.json(result)
    except Exception as e:
        st.error(f"명령어 실행에 실패했습니다: {str(e)}")

# 에이전트 등록
st.header("에이전트 등록")
with st.form("agent_registration"):
    name = st.text_input("에이전트 이름")
    description = st.text_area("설명")
    model = st.selectbox("모델", ["gpt-4", "gpt-3.5-turbo", "claude-3"])
    system_prompt = st.text_area("시스템 프롬프트")
    
    if st.form_submit_button("등록"):
        try:
            config = {
                "name": name,
                "description": description,
                "model": model,
                "system_prompt": system_prompt
            }
            result = register_agent(config)
            st.success("에이전트가 등록되었습니다.")
            st.json(result)
        except Exception as e:
            st.error(f"에이전트 등록에 실패했습니다: {str(e)}")

# 성능 모니터링
st.header("성능 모니터링")
try:
    # 샘플 데이터 생성 (실제로는 API에서 가져와야 함)
    dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now())
    data = {
        "date": dates,
        "cpu_usage": [30, 45, 60, 40, 50, 35, 55],
        "memory_usage": [40, 50, 65, 45, 55, 40, 60]
    }
    df = pd.DataFrame(data)
    
    # CPU 사용량 차트
    fig_cpu = px.line(df, x="date", y="cpu_usage", title="CPU 사용량")
    st.plotly_chart(fig_cpu)
    
    # 메모리 사용량 차트
    fig_memory = px.line(df, x="date", y="memory_usage", title="메모리 사용량")
    st.plotly_chart(fig_memory)
except Exception as e:
    st.error(f"성능 데이터를 표시하는데 실패했습니다: {str(e)}")

# 자가 개선 루프 UI (모델/프롬프트 선택 확장)
st.header("자가 개선 루프 (Human-in-the-loop)")

if 'preview' not in st.session_state:
    st.session_state['preview'] = None
if 'suggestions' not in st.session_state:
    st.session_state['suggestions'] = None
if 'approved_files' not in st.session_state:
    st.session_state['approved_files'] = []

# LLM 모델 선택 및 프롬프트 입력
llm_model = st.selectbox(
    "LLM 모델 선택",
    [
        "gpt-4o (대부분의 업무에 탁월함)",
        "o3 (고급 이성 사용)",
        "o3-pro (최고 성능의 이성)",
        "o4-mini (고급 이성에 가장 빠름)",
        "o4-mini-high (코딩 및 시각적 이성에 탁월함)"
    ]
)
# 내부적으로 모델명만 추출
llm_model_map = {
    "gpt-4o (대부분의 업무에 탁월함)": "gpt-4o",
    "o3 (고급 이성 사용)": "o3",
    "o3-pro (최고 성능의 이성)": "o3-pro",
    "o4-mini (고급 이성에 가장 빠름)": "o4-mini",
    "o4-mini-high (코딩 및 시각적 이성에 탁월함)": "o4-mini-high"
}
llm_model_selected = llm_model_map[llm_model]
custom_prompt = st.text_area("개선 프롬프트(옵션)", "")

# 1. 프리뷰(diff/patch 목록)
if st.button("자가 개선 diff/patch 프리뷰"):
    try:
        payload = {"model": llm_model_selected, "custom_prompt": custom_prompt}
        resp = requests.post(f"{API_URL}/self_improve/preview", headers=get_headers(), json=payload)
        st.session_state['preview'] = resp.json()
        analysis = resp.json()
        st.session_state['suggestions'] = analysis.get('preview', [])
    except Exception as e:
        st.error(f"프리뷰 실패: {str(e)}")

if st.session_state['preview']:
    st.subheader(":sparkles: 개선 diff/patch 목록 (승인할 항목 선택)")
    approved = []
    preview_list = st.session_state['preview'].get('preview', [])
    if len(preview_list) == 0:
        st.success("AI가 제안한 개선 diff/patch가 없습니다.\n\n✅ 최근 코드/테스트 상태가 양호합니다!\n필요시 직접 개선 요청을 해보세요.")
    else:
        import difflib
        import streamlit.components.v1 as components
        reason_inputs = {}
        for i, item in enumerate(preview_list):
            with st.expander(f"{item['file']}"):
                diff_html = f"<pre style='background:#222;color:#eee;padding:8px;border-radius:6px;overflow-x:auto'>{item['diff']}</pre>"
                components.html(diff_html, height=180)
                st.caption(f"**AI 리뷰:** {item.get('description', '')}")
                col1, col2 = st.columns([1,2])
                with col1:
                    approved_flag = st.checkbox(f"✅ 승인 (#{i+1})", key=f"approve_{i}")
                with col2:
                    reason = st.text_input(f"(선택) 승인/거부 사유 입력", key=f"reason_{i}")
                if approved_flag:
                    item_with_reason = dict(item)
                    item_with_reason['approval_reason'] = reason
                    approved.append(item_with_reason)
                reason_inputs[i] = reason
        st.session_state['approved_files'] = approved
        st.info(f"총 {len(preview_list)}개 중 승인 {len(approved)}개 선택됨.")
        if st.button(":rocket: 선택한 항목 적용(Apply)"):
            with st.spinner("AI 개선안 적용 및 테스트 중..."):
                try:
                    apply_payload = {
                        "suggestions": {"suggestions": preview_list},
                        "approved_files": approved,
                        "model": llm_model_selected,
                        "custom_prompt": custom_prompt
                    }
                    resp = requests.post(f"{API_URL}/self_improve/apply", headers=get_headers(), json=apply_payload)
                    result = resp.json()
                    # 적용 결과/테스트 결과 실시간 Alert
                    if result.get("test_result", {}).get("success", False):
                        st.success(f"✅ 적용 및 테스트 성공!\n{result.get('test_result', {}).get('summary', '')}")
                    else:
                        st.error(f"❌ 적용 또는 테스트 실패!\n{result.get('test_result', {}).get('summary', '')}")
                    st.json(result)
                except Exception as e:
                    st.error(f"적용 실패: {str(e)}")

# 2. 롤백 UI
st.subheader("롤백 (지정 파일/시점으로 복원)")
with st.form("rollback_form"):
    file = st.text_input("롤백할 파일 경로 (예: src/agents/example.py)")
    timestamp = st.text_input("백업 타임스탬프 (예: 20240601_153000)")
    if st.form_submit_button("롤백 실행"):
        try:
            payload = {"file": file, "timestamp": timestamp}
            resp = requests.post(f"{API_URL}/self_improve/rollback", headers=get_headers(), json=payload)
            st.success("롤백 결과:")
            st.json(resp.json())
        except Exception as e:
            st.error(f"롤백 실패: {str(e)}")

# 지식베이스(임베딩) 갱신 UI
st.header("지식베이스(임베딩) 갱신")
if st.button("지식베이스 임베딩 갱신 실행"):
    try:
        import sys
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data")))
        from embedding_pipeline import EmbeddingPipeline
        pipe = EmbeddingPipeline()
        indexed = pipe.embed_files(["../src/**/*.py", "../README.md"])
        st.success(f"임베딩 완료: {len(indexed)}개 파일")
        st.json(indexed)
    except Exception as e:
        st.error(f"임베딩 갱신 실패: {str(e)}")

# 개선 이력/테스트 결과/성능 지표 시각화
st.header("운영 모니터링 및 개선 이력")
try:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data")))
    from pipeline import DataPipeline, DataConfig
    db_path = os.environ.get("DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "agent.db")))
    pipe = DataPipeline(DataConfig(
        input_path="../data/input",
        output_path="../data/output",
        db_path=db_path
    ))
    # 개선 이력
    st.subheader(":memo: 자가 개선 변경 이력 (selfimprove_history)")
    try:
        df_si = pd.read_sql_query("SELECT * FROM selfimprove_history ORDER BY timestamp DESC LIMIT 100", pipe.conn)
        if not df_si.empty:
            df_si['status'] = df_si['diff'].apply(lambda d: '적용' if d else '실패')
            st.dataframe(df_si.style.applymap(lambda v: 'background-color: #d4edda' if v=='적용' else 'background-color: #f8d7da', subset=['status']))
            st.markdown(f"**최근 개선 건수:** {len(df_si)}  |  **최근 변경 파일:** `{df_si.iloc[0]['file']}` / {df_si.iloc[0]['timestamp']}")
        else:
            st.info("최근 개선 이력이 없습니다.")
    except Exception as e:
        st.info(f"개선 이력 조회 실패: {str(e)}")
    # 테스트 결과(agent_logs)
    st.subheader(":test_tube: 에이전트 액션/테스트 로그 (agent_logs)")
    try:
        df_hist = pipe.get_agent_logs()
        if not df_hist.empty:
            if 'status' in df_hist.columns:
                total_tests = len(df_hist)
                passed = (df_hist['status'] == 'success').sum()
                st.markdown(f"**테스트 통과율:** :green[{passed}/{total_tests}]  ")
                st.progress(passed/total_tests if total_tests else 0)
            st.dataframe(df_hist)
        else:
            st.info("테스트 로그가 없습니다.")
    except Exception as e:
        st.info(f"테스트 로그 조회 실패: {str(e)}")
    # 성능 지표(performance_metrics)
    st.subheader(":bar_chart: 성능 지표 (performance_metrics)")
    try:
        df_perf = pd.read_sql_query("SELECT * FROM performance_metrics ORDER BY timestamp DESC LIMIT 100", pipe.conn)
        if not df_perf.empty:
            st.dataframe(df_perf)
            st.line_chart(df_perf.set_index("timestamp")[['cpu_usage', 'memory_usage']])
        else:
            st.info("성능 지표 데이터가 없습니다.")
    except Exception as e:
        st.info(f"성능 지표 조회 실패: {str(e)}")
    # 자동 리포트 생성 섹션
    st.header(":clipboard: 자동 리포트 (개선 루프 요약)")
    try:
        # 개선 이력 요약
        df_si = pd.read_sql_query("SELECT * FROM selfimprove_history ORDER BY timestamp DESC LIMIT 100", pipe.conn)
        total_changes = len(df_si)
        last_change = df_si.iloc[0] if not df_si.empty else None
        st.markdown(f"**최근 개선 건수:** {total_changes}")
        if last_change is not None:
            st.markdown(f"**최근 변경 파일:** `{last_change['file']}` / {last_change['timestamp']}")
        # 테스트 통과율
        df_logs = pipe.get_agent_logs()
        if not df_logs.empty and 'status' in df_logs.columns:
            total_tests = len(df_logs)
            passed = (df_logs['status'] == 'success').sum()
            st.markdown(f"**테스트 통과율:** :green[{passed}/{total_tests}]  ")
            st.progress(passed/total_tests if total_tests else 0)
        # 최근 커밋/PR (간단 요약)
        st.markdown("**최근 커밋/PR(예시):**")
        try:
            import subprocess
            repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            log = subprocess.check_output(["git", "log", "--oneline", "-5"], cwd=repo_path, encoding="utf-8")
            st.code(log, language="bash")
        except Exception as e:
            st.info(f"Git 로그 조회 실패: {str(e)}")
    except Exception as e:
        st.info(f"자동 리포트 생성 실패: {str(e)}")
    pipe.close()
except Exception as e:
    st.info(f"DB 연결/조회 실패: {str(e)}") 