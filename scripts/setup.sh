#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}AI 에이전트 개발 환경 설정을 시작합니다...${NC}"

# Python 3.12 설치 확인
if ! command -v python3.12 &> /dev/null; then
    echo -e "${YELLOW}Python 3.12 설치 중...${NC}"
    sudo apt update
    sudo apt install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.12 python3.12-venv
fi

# 가상환경 생성
echo -e "${YELLOW}Python 가상환경 생성 중...${NC}"
python3.12 -m venv venv
source venv/bin/activate

# pip 업그레이드
echo -e "${YELLOW}pip 업그레이드 중...${NC}"
pip install --upgrade pip

# 의존성 설치
echo -e "${YELLOW}프로젝트 의존성 설치 중...${NC}"
pip install -r requirements.txt

# Docker 컨테이너 실행
echo -e "${YELLOW}Docker 컨테이너 시작 중...${NC}"
docker compose up -d

# 디렉토리 구조 생성
echo -e "${YELLOW}프로젝트 디렉토리 구조 생성 중...${NC}"
mkdir -p src/{agents,core,utils}
mkdir -p tests
touch src/__init__.py
touch tests/__init__.py

# 권한 설정
echo -e "${YELLOW}스크립트 실행 권한 설정 중...${NC}"
chmod +x scripts/*.sh

echo -e "${GREEN}설정이 완료되었습니다!${NC}"
echo -e "${YELLOW}다음 단계:${NC}"
echo "1. 가상환경 활성화: source venv/bin/activate"
echo "2. 테스트 실행: pytest"
echo "3. 개발 서버 시작: streamlit run src/app.py" 