# Palantir AI Platform

## 프로젝트 개요
- FastAPI 기반 백엔드 API, 데이터 파이프라인, 인증, 모니터링, 문서화 등 복합 시스템
- PostgreSQL, Weaviate, Prometheus, Grafana, MkDocs, Pytest 등 최신 스택

## 개발 환경 및 의존성
- **WSL2 Ubuntu 환경 강력 권장** (PowerShell/Windows 환경에서는 일부 명령어/도구 미지원)
- Python 3.12 이상, venv + pip 기반 가상환경 사용
- 모든 의존성은 requirements.txt 단일 파일로 관리 (dev/prod 통합)
- 불필요한 폴더/파일/스크립트/설정(archive, apps/reflex_ui, site, setup_offline.sh, weaviate_boot.py, config/pylintrc_utf8.ini, promptfooconfig.yaml 등) 완전 삭제

## 빠른 시작
```bash
# 1. 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 2. 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# 3. 서비스 실행 (도커)
docker-compose up -d --build

# 4. DB 마이그레이션
alembic upgrade head

# 5. 전체 테스트
pytest

# 6. 서버 실행
uvicorn main:app --host 0.0.0.0 --port 8000

# 7. 상태 확인
curl http://localhost:8000/api/status
```

## 문서 및 아키텍처
- 개발자 가이드: docs/DEVELOPER_GUIDE.md
- MkDocs 기반 정적 문서: mkdocs serve/build
- 시스템 아키텍처 다이어그램 자동 생성: scripts/generate_architecture_diagram.py

## 기타
- 신규 개발자 온보딩, 운영/모니터링, 테스트/품질 자동화, 문서화 등은 docs/ 및 Makefile 참고

### User Interface
본 프로젝트의 메인 UI는 Reflex 프레임워크를 기반으로 하며, `apps/reflex_ui` 디렉토리에서 관리됩니다. 모든 핵심 기능(데이터 탐색, 파이프라인 빌드, 모니터링)은 Reflex UI를 통해 제공됩니다. 초기 프로토타입으로 개발되었던 Streamlit UI는 `archive/streamlit_ui`에 보관되어 있습니다.
