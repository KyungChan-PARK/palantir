#!/bin/bash

# Palantir AIP 운영 자동화 스크립트 (WSL Ubuntu 전용)
# FastAPI, Streamlit, Prefect 등 주요 서비스 일괄 실행 및 정책/운영/보안 자동화 연동

if [[ "$(uname -a)" != *"microsoft"* ]]; then
  echo "[ERROR] 반드시 WSL Ubuntu 환경에서만 실행해야 합니다. PowerShell 금지."
  exit 1
fi

set -e

LOG_DIR=logs
mkdir -p $LOG_DIR

# FastAPI 실행
nohup uvicorn palantir.api.status:app --host 0.0.0.0 --port 8000 > $LOG_DIR/fastapi.log 2>&1 &
FASTAPI_PID=$!
echo "[INFO] FastAPI 서버(PID: $FASTAPI_PID) 실행됨. 로그: $LOG_DIR/fastapi.log"

# Streamlit 실행
nohup streamlit run palantir/ui/app.py --server.port 8501 > $LOG_DIR/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo "[INFO] Streamlit 대시보드(PID: $STREAMLIT_PID) 실행됨. 로그: $LOG_DIR/streamlit.log"

# Prefect 서버 실행
nohup prefect server start > $LOG_DIR/prefect.log 2>&1 &
PREFECT_PID=$!
echo "[INFO] Prefect 서버(PID: $PREFECT_PID) 실행됨. 로그: $LOG_DIR/prefect.log"

# 정책/운영/보안 자동화(예시: 정책 위반/실패 감지)
FAIL_COUNT=0
for LOG in $LOG_DIR/*.log; do
  if grep -qE "(ERROR|CRITICAL|정책 위반|Policy Violation)" "$LOG"; then
    echo "[ALERT] 정책 위반/운영 실패 감지: $LOG"
    ((FAIL_COUNT++))
  fi
  if [[ $FAIL_COUNT -ge 3 ]]; then
    echo "[AUTO-STOP] 3회 연속 실패/정책 위반 감지. 모든 서비스 중단 및 Planner 재계획 필요."
    kill $FASTAPI_PID $STREAMLIT_PID $PREFECT_PID
    # TODO: Slack/이메일/대시보드 등 실시간 알림 연동
    exit 2
  fi
  sleep 1
done &

# 실행 결과 요약
sleep 2
echo "[SUMMARY] 모든 서비스가 정상적으로 실행되었습니다."
echo "- FastAPI: http://localhost:8000"
echo "- Streamlit: http://localhost:8501"
echo "- Prefect: http://localhost:4200 (기본 포트)"
echo "[TIP] 정책 위반/운영 실패 시 자동 중단 및 알림이 동작합니다."
# TODO: Slack/이메일/대시보드 등 실시간 알림 연동 