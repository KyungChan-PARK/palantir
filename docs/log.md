# Palantir 프로젝트 고도화 진행 로그

## 1. 프로젝트 구조 및 WSL2 환경 준비
- WSL2 Ubuntu 22.04, Poetry, Docker Desktop 등 개발 환경 준비 및 이슈 해결
- Docker 미사용 환경에서 SQLite로 Alembic 마이그레이션 우회 적용

## 2. 문서·가이드 자동화 (Phase 1)
- diagrams 패키지로 아키텍처 다이어그램 자동 생성
- MkDocs material 테마로 정적 사이트 배포 및 문서 자동화 안내 추가

## 3. 하이브리드 개발 모델 강화 (Phase 2)
- SDK 파이프라인 컴포넌트 베이스 클래스 및 registry 데코레이터, components.json 자동 갱신 구현
- 단위 테스트, Reflex UI 파이프라인 빌더 연동, YAML ↔ 시각 노드 변환 함수 및 테스트 구현

## 4. 온톨로지 액션 엔진 (Phase 3)
- Prefect 서버/에이전트 서비스 추가, 샘플 플로우 작성 및 Prefect UI 등록
- OntologyAction 모델 확장, Alembic 마이그레이션 우회 적용
- ActionExecutor, FastAPI 라우터(POST /actions/{id}/trigger) 구현

## 5. 실시간 스트리밍 + RAG 파이프라인 (Phase 4, 일부)
- Prefect 기반 RAG ingestion flow(Kafka → chunk → embed → Weaviate) 작성
- kafka_consumer에서 rag_ingestion_flow 연동(10개씩 배치 처리)

## 6. RAG RetrievalQA 체인 유틸리티 구현 (진행)
- palantir/core/rag_pipeline.py에 Weaviate + LLM 기반 RetrievalQA 체인(get_rag_qa_chain, run_rag_qa) 함수 신규 구현
- LangChain의 WeaviateVectorStore, OpenAIEmbeddings, ChatOpenAI, RetrievalQA 활용

## 7. /ask RAG 모드 FastAPI 엔드포인트 구현 (진행)
- palantir/api/ask.py에서 mode가 'rag'일 때 palantir.core.rag_pipeline.run_rag_qa를 호출하여 RAG QA 결과 반환 분기 추가
- 환경변수(WEAVIATE_URL, OPENAI_API_KEY) 사용, 예외 처리 및 소스 반환 포함

## 8. promptfoo 평가 자동화 연동 (진행)
- promptfooconfig.yaml: /ask RAG API 평가용 promptfoo 설정파일 생성 (providers, tests, assert 포함)
- scripts/run_promptfoo_eval.py: promptfoo CLI를 통해 평가 자동 실행하는 스크립트 작성

## Phase 1.1 Loki 로깅 통합 (진행)
- requirements.txt에 loguru, loguru-handler-loki, asgi-correlation-id 패키지 추가
- palantir/core/logging_config.py: setup_logger 함수로 LokiHandler 등록, 환경변수(LOKI_URL) 지원, JSON serialize
- palantir/main.py: 앱 시작 시 setup_logger 호출, CorrelationIdMiddleware 추가

## loguru + Loki + 표준 logging + warnings + print 통합 리디렉션 (최신 best practice 적용)
- InterceptHandler로 logging 모듈 로그를 loguru로 통합
- warnings.showwarning을 loguru로 포워딩
- logger.add(sys.stderr, serialize=True)로 콘솔 로그도 JSON 출력

## 9. WSL2/Ubuntu 환경 전환 및 용량 최적화 (2025-06-11)
- PowerShell/Windows 환경에서 리눅스 명령어 및 도커 명령이 정상 동작하지 않아 WSL2 Ubuntu 환경으로 전환
- 불필요한 테스트/캐시/DB/로그/가상환경 파일(.venv, __pycache__, .pytest_cache, .mypy_cache, .coverage, .hypothesis, .cache, *.pyc, *.pyo, *.db, *.log 등) 및 Postgres 데이터(sudo rm -rf ./data/postgres) 완전 삭제로 용량 최적화
- requirements.txt/requirements-dev.txt 분리 및 passlib, promptfoo 등 PyPI 버전 이슈 해결(최신 지원 버전으로 수정)
- docker buildx 미설치 시 설치, 환경변수 미설정 시 경고, alembic/pytest/uvicorn 등 실제 실행 및 검증 절차 명확화
- 모든 작업은 WSL2 Ubuntu 환경에서만 완전 자동화/최적화 가능함을 명시

---

**다음 작업:**
- RetrievalQA 체인 구현 (Weaviate → LLM QA)
- /ask RAG 모드 API 구현
- promptfoo 평가 자동화 연동 