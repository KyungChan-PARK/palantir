#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 상태 출력 함수
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}[OK]${NC} $2"
    else
        echo -e "${RED}[FAIL]${NC} $2"
    fi
}

# 경고 출력 함수
print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo "=== Palantir 시스템 상태 점검 ==="
echo "실행 시간: $(date)"
echo

# 1. 디스크 공간 확인
echo "=== 디스크 공간 확인 ==="
df -h / | tail -n 1
DISK_USAGE=$(df -h / | tail -n 1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    print_warning "디스크 사용량이 90%를 초과했습니다"
fi
echo

# 2. 메모리 상태 확인
echo "=== 메모리 상태 확인 ==="
free -h
MEMORY_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ $MEMORY_USAGE -gt 90 ]; then
    print_warning "메모리 사용량이 90%를 초과했습니다"
fi
echo

# 3. 프로세스 확인
echo "=== 프로세스 상태 확인 ==="
ps aux | grep -E "python|palantir" | grep -v grep
print_status $? "Palantir 프로세스 확인"
echo

# 4. 포트 확인
echo "=== 포트 상태 확인 ==="
netstat -tulpn 2>/dev/null | grep -E ":(80|443|8000|9090|3000)"
print_status $? "필수 포트 확인"
echo

# 5. 로그 파일 확인
echo "=== 로그 파일 확인 ==="
LOG_DIR="../logs"
if [ -d "$LOG_DIR" ]; then
    ls -lh "$LOG_DIR"
    # 최근 오류 로그 확인
    echo "최근 오류 로그:"
    tail -n 5 "$LOG_DIR"/palantir.log 2>/dev/null | grep -i "error"
else
    print_warning "로그 디렉토리를 찾을 수 없습니다"
fi
echo

# 6. 설정 파일 확인
echo "=== 설정 파일 확인 ==="
CONFIG_FILES=("../config/default.yaml" "../config/offline.yaml" "../config/logging.yaml" "../config/security.yaml")
for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_status 0 "$(basename "$file") 존재함"
    else
        print_status 1 "$(basename "$file") 없음"
    fi
done
echo

# 7. 데이터베이스 상태 확인
echo "=== 데이터베이스 상태 확인 ==="
if [ -f "../users.db" ]; then
    print_status 0 "users.db 존재함"
    ls -lh "../users.db"
else
    print_status 1 "users.db 없음"
fi
echo

# 8. Docker 상태 확인
echo "=== Docker 상태 확인 ==="
if command -v docker &> /dev/null; then
    docker ps
    print_status $? "Docker 컨테이너 상태"
else
    print_warning "Docker가 설치되지 않았습니다"
fi
echo

# 9. 네트워크 연결 확인
echo "=== 네트워크 연결 확인 ==="
ping -c 1 localhost > /dev/null
print_status $? "로컬호스트 연결"
echo

# 10. 보안 상태 확인
echo "=== 보안 상태 확인 ==="
# 파일 권한 확인
find .. -type f -name "*.py" -perm /o=w 2>/dev/null
if [ $? -eq 0 ]; then
    print_warning "일부 Python 파일이 전체 쓰기 권한을 가지고 있습니다"
else
    print_status 0 "파일 권한 정상"
fi

echo
echo "=== 점검 완료 ==="
echo "자세한 로그는 $LOG_DIR/health_check.log를 확인하세요" 