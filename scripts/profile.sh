#!/bin/bash

# 프로파일링 설정
PROFILE_DIR="../logs/profiles"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PROFILE_FILE="$PROFILE_DIR/profile_$TIMESTAMP"

# 프로파일링 디렉토리 생성
mkdir -p "$PROFILE_DIR"

# Python 프로파일링 함수
profile_python() {
    echo "=== Python 프로파일링 시작 ==="
    # cProfile을 사용한 프로파일링
    python3 -m cProfile -o "${PROFILE_FILE}.pstats" ../main.py &
    PID=$!
    sleep 30
    kill $PID

    # 결과 분석
    python3 -c "
import pstats
from pstats import SortKey
p = pstats.Stats('${PROFILE_FILE}.pstats')
p.strip_dirs().sort_stats(SortKey.TIME).print_stats(20)
" > "${PROFILE_FILE}_python.txt"
    
    echo "Python 프로파일링 결과: ${PROFILE_FILE}_python.txt"
}

# 메모리 프로파일링 함수
profile_memory() {
    echo "=== 메모리 프로파일링 시작 ==="
    # memory_profiler를 사용한 메모리 프로파일링
    python3 -m memory_profiler ../main.py > "${PROFILE_FILE}_memory.txt" &
    PID=$!
    sleep 30
    kill $PID
    
    echo "메모리 프로파일링 결과: ${PROFILE_FILE}_memory.txt"
}

# CPU 프로파일링 함수
profile_cpu() {
    echo "=== CPU 프로파일링 시작 ==="
    # top 명령어를 사용한 CPU 사용량 모니터링
    top -b -n 30 -d 1 | grep -E "python|palantir" > "${PROFILE_FILE}_cpu.txt"
    echo "CPU 프로파일링 결과: ${PROFILE_FILE}_cpu.txt"
}

# 디스크 I/O 프로파일링 함수
profile_io() {
    echo "=== 디스크 I/O 프로파일링 시작 ==="
    # iostat를 사용한 디스크 I/O 모니터링
    iostat -x 1 30 > "${PROFILE_FILE}_io.txt"
    echo "디스크 I/O 프로파일링 결과: ${PROFILE_FILE}_io.txt"
}

# 네트워크 프로파일링 함수
profile_network() {
    echo "=== 네트워크 프로파일링 시작 ==="
    # nethogs를 사용한 네트워크 사용량 모니터링
    nethogs -t -c 30 > "${PROFILE_FILE}_network.txt" 2>/dev/null
    echo "네트워크 프로파일링 결과: ${PROFILE_FILE}_network.txt"
}

# 데이터베이스 프로파일링 함수
profile_database() {
    echo "=== 데이터베이스 프로파일링 시작 ==="
    # SQLite 데이터베이스 성능 분석
    echo ".timer on" > "${PROFILE_FILE}_db.sql"
    echo "EXPLAIN QUERY PLAN SELECT * FROM users;" >> "${PROFILE_FILE}_db.sql"
    echo "ANALYZE;" >> "${PROFILE_FILE}_db.sql"
    sqlite3 ../users.db < "${PROFILE_FILE}_db.sql" > "${PROFILE_FILE}_database.txt"
    echo "데이터베이스 프로파일링 결과: ${PROFILE_FILE}_database.txt"
}

# 전체 프로파일링 실행
echo "=== Palantir 성능 프로파일링 시작 ==="
echo "시작 시간: $(date)"
echo "프로파일 디렉토리: $PROFILE_DIR"
echo

# 각 프로파일링 실행
profile_python
profile_memory
profile_cpu
profile_io
profile_network
profile_database

# 결과 요약
echo
echo "=== 프로파일링 완료 ==="
echo "완료 시간: $(date)"
echo "결과 파일:"
ls -lh "$PROFILE_DIR/profile_$TIMESTAMP"*

# 결과 분석 및 리포트 생성
echo
echo "=== 성능 분석 리포트 생성 ==="
{
    echo "# Palantir 성능 분석 리포트"
    echo "## 실행 정보"
    echo "- 실행 시간: $(date)"
    echo "- 프로파일 ID: $TIMESTAMP"
    echo
    echo "## Python 성능"
    tail -n 20 "${PROFILE_FILE}_python.txt"
    echo
    echo "## 메모리 사용량"
    tail -n 10 "${PROFILE_FILE}_memory.txt"
    echo
    echo "## CPU 사용량"
    tail -n 10 "${PROFILE_FILE}_cpu.txt"
    echo
    echo "## 디스크 I/O"
    tail -n 10 "${PROFILE_FILE}_io.txt"
    echo
    echo "## 네트워크 사용량"
    tail -n 10 "${PROFILE_FILE}_network.txt"
    echo
    echo "## 데이터베이스 성능"
    cat "${PROFILE_FILE}_database.txt"
} > "${PROFILE_FILE}_report.md"

echo "성능 분석 리포트가 생성되었습니다: ${PROFILE_FILE}_report.md" 