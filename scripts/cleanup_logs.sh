#!/bin/bash

# 로그 설정
LOG_DIR="../logs"
PROFILE_DIR="$LOG_DIR/profiles"
BACKUP_DIR="$LOG_DIR/backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"

echo "=== 로그 파일 정리 시작 ==="
echo "시작 시간: $(date)"
echo

# 오래된 로그 파일 백업 (7일 이상)
echo "=== 오래된 로그 파일 백업 ==="
find "$LOG_DIR" -type f -name "*.log" -mtime +7 -exec mv {} "$BACKUP_DIR" \;
echo "7일 이상 된 로그 파일을 $BACKUP_DIR로 이동했습니다"

# 오래된 프로파일 결과 정리 (30일 이상)
echo
echo "=== 오래된 프로파일 결과 정리 ==="
if [ -d "$PROFILE_DIR" ]; then
    find "$PROFILE_DIR" -type f -mtime +30 -delete
    echo "30일 이상 된 프로파일 결과를 삭제했습니다"
else
    echo "프로파일 디렉토리가 존재하지 않습니다"
fi

# 로그 파일 압축
echo
echo "=== 로그 파일 압축 ==="
cd "$BACKUP_DIR" || exit
tar -czf "logs_backup_$TIMESTAMP.tar.gz" ./*.log 2>/dev/null
if [ $? -eq 0 ]; then
    # 압축 성공 시 원본 삭제
    rm ./*.log
    echo "백업 로그 파일을 압축했습니다: logs_backup_$TIMESTAMP.tar.gz"
else
    echo "압축할 로그 파일이 없습니다"
fi

# 오래된 백업 삭제 (90일 이상)
echo
echo "=== 오래된 백업 삭제 ==="
find "$BACKUP_DIR" -type f -name "logs_backup_*.tar.gz" -mtime +90 -delete
echo "90일 이상 된 백업 파일을 삭제했습니다"

# 로그 통계 출력
echo
echo "=== 로그 정리 통계 ==="
echo "현재 로그 디렉토리 크기:"
du -sh "$LOG_DIR"
echo
echo "현재 백업 디렉토리 크기:"
du -sh "$BACKUP_DIR"
echo
echo "남은 디스크 공간:"
df -h "$LOG_DIR" | tail -n 1

echo
echo "=== 로그 파일 정리 완료 ==="
echo "완료 시간: $(date)" 