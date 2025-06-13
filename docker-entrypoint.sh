#!/bin/bash
set -e

# 환경 변수 확인
if [ -z "$API_KEY" ]; then
    echo "Error: API_KEY environment variable is not set"
    exit 1
fi

if [ -z "$DB_PATH" ]; then
    echo "Error: DB_PATH environment variable is not set"
    exit 1
fi

# 디렉토리 생성
mkdir -p $(dirname $DB_PATH)
mkdir -p /app/data/input
mkdir -p /app/data/output

# 서비스 시작
case "$1" in
    "api")
        echo "Starting FastAPI server..."
        uvicorn src.api.main:app --host 0.0.0.0 --port 8000
        ;;
    "dashboard")
        echo "Starting Streamlit dashboard..."
        streamlit run src/dashboard/app.py --server.port 8501 --server.address 0.0.0.0
        ;;
    *)
        echo "Usage: $0 {api|dashboard}"
        exit 1
        ;;
esac 