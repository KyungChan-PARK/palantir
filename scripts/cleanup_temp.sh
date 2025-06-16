#!/bin/bash

# 임시 파일 설정
TEMP_DIRS=(
    "../data/temp"
    "../logs/temp"
    "/tmp/palantir"
    "../.pytest_cache"
    "../**/__pycache__"
    "../**/*.pyc"
    "../**/*.pyo"
    "../**/*.pyd"
    "../**/.coverage"
    "../**/.pytest_cache"
    "../**/.mypy_cache"
    "../**/.ruff_cache"
)

echo "=== 임시 파일 정리 시작 ==="
echo "시작 시간: $(date)"
echo

# 각 임시 디렉토리 정리
for dir in "${TEMP_DIRS[@]}"; do
    echo "=== $dir 정리 중 ==="
    if [ -e "$dir" ]; then
        # 디렉토리 크기 출력
        echo "정리 전 크기:"
        du -sh "$dir" 2>/dev/null
        
        # 파일 삭제
        if [ -d "$dir" ]; then
            rm -rf "$dir"
            echo "디렉토리를 삭제했습니다"
        else
            rm -f "$dir"
            echo "파일을 삭제했습니다"
        fi
    else
        echo "대상이 존재하지 않습니다"
    fi
    echo
done

# Python 캐시 파일 정리
echo "=== Python 캐시 파일 정리 ==="
find .. -type f -name "*.py[cod]" -delete
find .. -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
echo "Python 캐시 파일을 정리했습니다"
echo

# 테스트 캐시 정리
echo "=== 테스트 캐시 정리 ==="
find .. -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find .. -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null
echo "테스트 캐시를 정리했습니다"
echo

# 린터 캐시 정리
echo "=== 린터 캐시 정리 ==="
find .. -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null
find .. -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null
echo "린터 캐시를 정리했습니다"
echo

# Docker 임시 파일 정리
echo "=== Docker 임시 파일 정리 ==="
if command -v docker &> /dev/null; then
    # 사용하지 않는 볼륨 정리
    docker volume prune -f
    # 중단된 컨테이너 정리
    docker container prune -f
    # 태그 없는 이미지 정리
    docker image prune -f
    echo "Docker 임시 파일을 정리했습니다"
else
    echo "Docker가 설치되지 않았습니다"
fi
echo

# 디스크 사용량 확인
echo "=== 디스크 사용량 확인 ==="
echo "현재 프로젝트 디렉토리 크기:"
du -sh .. 2>/dev/null
echo
echo "남은 디스크 공간:"
df -h . | tail -n 1

echo
echo "=== 임시 파일 정리 완료 ==="
echo "완료 시간: $(date)" 