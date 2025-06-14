# Palantir.Zip 개발로그 (DEVLOG.md)

## 1. 프로젝트 개요 및 비전
- 1인 개발자가 WSL Ubuntu 환경에서 완전 자동화 자가개선형 AI 시스템을 구축하는 것을 목표로 함
- 멀티에이전트 오케스트레이션(Planner, Developer, Reviewer, SelfImprover) + MCP 계층 + 온톨로지/ETL/ML/임베딩/DB/대시보드/API/문서화 통합
- Cursor AI, LangGraph, 최신 LLM(특히 o4-mini-high), MCP 서버, ChromaDB, FastAPI, Streamlit 등 2025년 기준 최신 기술 적극 도입

## 2. 아키텍처/설계 결정 및 주요 지침
- 첨부 문서(ai_aigent_orchestration.md, ai_agent_self_improvement.md, ai_agent.md) 기반으로 전체 구조/역할/자동화 루프/자가개선/정책/운영 전략 수립
- LangGraph 기반 오케스트레이터: Planner→Developer→Reviewer→SelfImprover 순서의 자동화 루프, Reviewer→SelfImprover→Reviewer 반복, 실패 시 Planner 재계획, 상태 관리
- MCP 계층: LLM, 파일, Git, 테스트, 웹 등 도구 추상화, FastAPI 기반 MCP 서버로 통합
- 온톨로지/지식그래프: Pydantic 기반 도메인 객체, 관계, 질의/분석/추천 API, Streamlit 대시보드 시각화
- ETL/ML/임베딩: Prefect 기반 데이터 파이프라인, DuckDB/SQLite/ChromaDB/MLflow 연동, 임베딩/분류/예측 결과 온톨로지 반영
- 정책/보안: .cursorrules, POLICY.md, FAQ.md, JWT 인증, 위험 명령 차단, 운영 자동화/모니터링

## 3. 단계별 개발 내역 (상세)

### 3.1 초기 환경/인프라 구축
- Python 3.12, WSL Ubuntu, Docker, FastAPI, Streamlit, Prefect, ChromaDB, MLflow 등 환경 세팅
- MCP 서버(LLM, File, Git, Test, Web MCP) 프로토타입 구현 및 통합
- Git 저장소/브랜치 전략/CI(CI/CD, pre-commit, pytest, lint, mypy) 설정

### 3.2 멀티에이전트/오케스트레이터/자동화 루프
- core/agents.py: Planner/Developer/Reviewer/SelfImprover 역할별 에이전트 클래스 구현, process(state) 인자화, 프롬프트/이력/실패/피드백 반영
- core/orchestrator.py: LangGraph 기반 오케스트레이터, Reviewer→SelfImprover→Reviewer 루프, 3회 실패 시 Planner 재계획, 상태 딕셔너리 관리, print/logging
- MCP 계층(services/mcp/): LLM, 파일, Git, 테스트, 웹 MCP 추상화, TestMCP에서 pytest/flake8/mypy 자동화, 결과 통합 반환

### 3.3 온톨로지/지식그래프/ETL/ML
- ontology/objects.py: Payment, Delivery, Event 등 실전 도메인 객체/관계/유효성 메서드 추가
- ontology/repository.py: NetworkX 기반 온톨로지 그래프, 객체/관계 CRUD/검색/연동
- ontology/api.py: FastAPI 기반 온톨로지 객체/관계/검색/분석 API, Payment/Delivery/Event 등 확장
- process/flows.py: Prefect 기반 ETL/임베딩/DB/ML 파이프라인, 실전 데이터 적재, 임베딩/분류/예측 결과 온톨로지 반영, 객체-관계 자동 생성

### 3.4 대시보드/API/운영 자동화
- ui/pages/agent_status.py: 에이전트 상태/테스트/로그/온톨로지/실시간 CRUD/관계/이벤트/임베딩/유사도 추천/네트워크 시각화 등 Streamlit 대시보드 구현
- api/ontology.py: 온톨로지 객체/관계/분석/추천 FastAPI API 구현
- run_all.sh: FastAPI, Streamlit, Prefect를 WSL Ubuntu에서 백그라운드로 실행하는 운영 자동화 스크립트 추가

### 3.5 정책/보안/문서화/운영
- .cursorrules, POLICY.md: 위험 명령 차단, 테스트/운영 자동화, 인증/권한, 운영 정책 명확화
- FAQ.md, USAGE_EXAMPLES.md, CONTRIBUTING.md: 실전 활용/운영/확장/테스트/보안/정책/기여 가이드 문서화
- README.md: 전체 구조/정책/운영/확장/테스트/문서화/자동화 최신화

## 4. 테스트/운영/실전 활용
- pytest, Prefect Flow, API, 대시보드, ETL/ML, 관계/이벤트 생성 등 통합 테스트 자동화
- Prometheus, Grafana, docker-compose 등 운영 모니터링/자동화
- 실전 데이터/관계/임베딩/이벤트/분석/추천/시각화/자동화까지 통합 운영

## 5. 주요 개선/의사결정/트러블슈팅 이력
- LangGraph 오케스트레이터 루프/분기/재계획/롤백 구조 고도화, 실패 시 Planner 재계획/분기/상태 관리
- MCP 계층을 Cursor MCP/내장 툴로 통합, 위험 명령 차단 정책 강화
- 온톨로지/ETL/ML/임베딩/관계/이벤트/분석/추천/시각화/자동화 등 실전 데이터 기반 확장
- 운영 자동화(run_all.sh), 정책/문서화/FAQ/기여 가이드 등 실전 운영/협업 기반 강화
- 각 단계별 주요 문제(테스트 실패, 데이터 연동 오류, 정책 위반 등) 발생 시 로그/FAQ/문서화로 해결 및 개선

## 6. 향후 계획 및 TODO
- 온톨로지/관계 기반 추천/분석/시각화 고도화, 실전 데이터/ML/임베딩 확장
- 운영/보안/정책/문서화/자동화 지속 강화, 실전 활용/협업/확장 지원
- 최신 LLM/멀티에이전트/오케스트레이션/자동화 트렌드 반영, 실전 운영/분석/추천/자동화 루프 고도화 