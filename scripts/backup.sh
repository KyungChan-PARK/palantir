#!/bin/bash

# 백업 설정
BACKUP_DIR="../backups"
DATA_DIR="../data"
CONFIG_DIR="../config"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 백업 타입 확인
if [ "$1" != "full" ] && [ "$1" != "incremental" ]; then
    echo "Usage: $0 [full|incremental]"
    exit 1
fi

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"

# 전체 백업
do_full_backup() {
    echo "Starting full backup..."
    BACKUP_FILE="$BACKUP_DIR/full_backup_$TIMESTAMP.tar.gz"
    tar -czf "$BACKUP_FILE" "$DATA_DIR" "$CONFIG_DIR"
    echo "Full backup completed: $BACKUP_FILE"
}

# 증분 백업
do_incremental_backup() {
    echo "Starting incremental backup..."
    LAST_BACKUP=$(ls -t "$BACKUP_DIR"/full_backup_*.tar.gz | head -n1)
    if [ -z "$LAST_BACKUP" ]; then
        echo "No full backup found. Performing full backup instead..."
        do_full_backup
        return
    fi
    
    BACKUP_FILE="$BACKUP_DIR/incremental_backup_$TIMESTAMP.tar.gz"
    find "$DATA_DIR" "$CONFIG_DIR" -newer "$LAST_BACKUP" -type f -print0 | \
        tar -czf "$BACKUP_FILE" --null -T -
    echo "Incremental backup completed: $BACKUP_FILE"
}

# 메인 로직
case "$1" in
    "full")
        do_full_backup
        ;;
    "incremental")
        do_incremental_backup
        ;;
esac

# 오래된 백업 정리 (30일 이상)
find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +30 -delete

echo "Backup process completed successfully" 