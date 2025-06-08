# Palantir-inspired AI Platform

이 프로젝트는 Palantir의 AIP와 유사한 개념의 지능형 데이터 분석 및 운영 플랫폼을 구축하는 것을 목표로 합니다. 온톨로지 기반의 데이터 통합, AI 모델 연동, 파이프라인 자동화 및 시각화 기능을 제공하여 데이터 기반 의사결정을 가속화합니다.

## 🏛️ 아키텍처 및 비전

본 프로젝트가 추구하는 기술적 비전과 아키텍처에 대한 자세한 내용은 **[Project Vision](./docs/project_vision.md)**에서 확인할 수 있습니다.

## 🚀 시작하기 (Getting Started)

프로젝트의 로컬 환경 설정, 설치, 실행 방법에 대한 자세한 가이드는 **[Deployment Guide](./docs/deployment.md)** 문서를 참고하십시오.

## 🏃 Quick Start

```bash
# 1. 의존성 설치
poetry install --no-interaction --with dev

# 2. Docker 서비스 기동 (DB · Kafka · Grafana 등)
docker-compose up -d

# 3. 개발 서버 실행
poetry run uvicorn main:app --reload --port 8000

# 4. Streamlit UI
poetry run palantir run ui  # CLI 확장 예정
```

서비스 기동 후 http://localhost:8000/docs 에서 OpenAPI 스펙을,
http://localhost:3000 에서 Grafana 대시보드를 확인할 수 있습니다.

## 核心コンポーネント (Core Components)

* `/palantir`: 핵심 비즈니스 로직과 도메인 모델이 포함된 소스 코드 루트입니다.
* `/apps`: Streamlit, Reflex 등 사용자에게 제공되는 프론트엔드 애플리케이션입니다.
* `/config`: 각종 설정 파일들을 중앙 관리하는 디렉토리입니다.
* `/docs`: 프로젝트의 모든 문서가 위치합니다.

## 📚 주요 문서 라이브러리

-   **[기여 가이드](./docs/CONTRIBUTING.md):** 버그 리포트, 코드 스타일, Pull Request 절차 등 프로젝트 기여 방법
-   **[API 레퍼런스](./docs/API_REFERENCE.md):** 사용 가능한 API 엔드포인트, 요청/응답 형식 명세
-   **[기능 요구사항 (PRD)](./docs/FEATURE_PRD.md):** 주요 기능에 대한 상세 정의서
-   **[문제 해결 가이드](./docs/troubleshooting.md):** 자주 발생하는 문제와 해결 방법 모음

## ✅ 품질 보증 (Quality Assurance)

프로젝트의 무결성을 검증하고 코드 품질을 유지하기 위해 다음 명령어를 실행하십시오:
```bash
# 모든 단위/통합 테스트 실행
pytest

# 코드 스타일 검사
pylint palantir/

# 타입 힌트 검사
mypy palantir/
```
