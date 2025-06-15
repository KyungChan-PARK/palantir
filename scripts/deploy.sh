#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 에러 처리
set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo -e "${RED}\"${last_command}\" command failed with exit code $?.${NC}"' EXIT

# 환경 변수 확인
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please create .env file from .env.example"
    exit 1
fi

# 디렉토리 생성
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p data/input data/output logs

# Docker 이미지 빌드
echo -e "${YELLOW}Building Docker images...${NC}"
docker-compose build

# 기존 컨테이너 중지 및 제거
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose down

# 새 컨테이너 시작
echo -e "${YELLOW}Starting new containers...${NC}"
docker-compose up -d

# 상태 확인
echo -e "${YELLOW}Checking container status...${NC}"
docker-compose ps

# 로그 확인
echo -e "${YELLOW}Checking container logs...${NC}"
docker-compose logs --tail=50

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "API is available at: ${YELLOW}http://localhost:8000${NC}"
echo -e "Dashboard is available at: ${YELLOW}http://localhost:8501${NC}"

# 성공 시 에러 트랩 제거
trap - EXIT 