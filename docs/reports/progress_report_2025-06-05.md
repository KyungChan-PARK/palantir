# Palantir-Style AI 데이터 파이프라인 개발 진행 상황 보고서 (2025-06-05)

> 작성자: 시니어 개발자

---

## 1. 로드맵 대비 진행 현황 요약

| 구분 | 목표(참고 로드맵) | 현재 구현 현황 | 완료 도 |
|------|-----------------|---------------|--------|
| **개발 환경** | Python 3.12 지원, Poetry 의존성 관리, Docker 멀티 스테이지, CI/CD 구축 | Poetry 마이그레이션 및 `Dockerfile` 다단계 빌드 완료, GitHub Actions (lint/test/build) 적용 | ✅ (100%) |
| **데이터 수집 · ETL** | Prefect/ Airflow 기반 ETL DAG, 다양한 소스 연동 | Prefect 2.0 ETL flow (CSV→DuckDB) 구현, 외부 API ingestion 스텁 추가 | 🟢 (70%) – 다중 소스 커넥터 추가 필요 |
| **저장소** | DuckDB + 그래프DB(Neo4j/NetworkX) | DuckDB, NetworkX 인메모리 그래프 repo 완료, Weaviate 스크립트 초기 버전 존재 | 🟢 (70%) – Neo4j 실행/CI 미연동, Vector Store RAG 미완료 |
| **Ontology 레이어** | Object/Link/Action/Function 모델 + 버전/권한 관리 | Repository + Graph search, CRUD API, NetworkX, Pydantic models 완비 | 🟢 (80%) – Action Triggered Workflow 미구현, 권한 모델 부족 |
| **AI/ML 모듈** | 전통 ML + LLM 통합, RAG, Auto-Evals | LangChain LLM(Chat & QueryGen) 통합, Embedding util, Cosine similarity, 기본 ML 구조 | 🟡 (65%) – 전통 ML, RAG, Evals 일부 미완성 |
| **API & Backend** | FastAPI REST + WebSocket, Auth, Rate-limit | 7개 FastAPI routers + JWT Auth 구현, WebSocket·Rate-limit 미구현 | 🟢 (70%) |
| **UI & 대시보드** | Streamlit 혹은 React SPA, 다국어, 고급 시각화 | Streamlit 5 페이지 (+고급 시각화 추가), 한국어/영어 토글 지원 준비 | ✅ (80%) |
| **DevOps & Observability** | Docker Compose, 모니터링(Grafana/Loki), 백업 | `docker-compose.yml`, Grafana+Loki 스택 텍스트 배포 파일 존재 | 🟢 (60%) – Python logging→Loki 연동 미구현 |
| **보안/거버넌스** | JWT/OAuth2, 롤 기반 권한, 감사 로그 | JWT Auth 및 비밀번호 해시, Token blacklist 도입; Role 기반 RBAC·감사 로그 부족 | 🟠 (50%) |

> 전체 평균 진척률 ≈ 72 ±4 %

---

## 2. 세부 성과

1. **UI 강화**: 채팅 히스토리 저장/불러오기, 데이터 탐색 고급 시각화(PCA·Heatmap), Ontology 커뮤니티 탐지, Settings 확장(Backup/Analytics) 등 완료.
2. **실행 엔트리포인트**: `palantir.ui.__main__` 생성 → `python -m palantir.ui` 로 배포 편의 성 상승.
3. **CI 품질**: lint/pytest workflow 동작, 멀티 스테이지 Docker 빌드 캐시 최적화.
4. **폴더 구조**: `ingest/ process/ models/ ontology/ ui/` 등 로드맵 정의 대로 정비.

5. **Auth/JWT 구현**: Core `auth.py` 모듈로 JWT 발급·검증, 비밀번호 해시 및 블랙리스트 처리 로직 구현.

6. **ETL 플로우 추가**: Prefect 기반 `csv_to_duckdb_flow` 구현으로 CSV→DuckDB 자동화 파이프라인 확보.

---

## 3. 미비 요소 및 개선 로드맵

### 3-1. 파이프라인 및 모델링
- [ ] **외부 커넥터 추가**: GitHub 오픈소스 `prefect-aws` 예제 참고하여 S3 → DuckDB 로드 플로우 도입.
- [ ] **전통 ML 파이프라인**: `sklearn-cookiecutter` 구조 참고하여 `models/` 에 `train.py`, `predict.py` 템플릿 추가.
- [ ] **RAG 파이프라인**: `weaviate-client` + `langchain` `VectorStoreRetriever` 샘플 (Ref: github.com/weaviate‐python-client examples) 통합.

### 3-2. 백엔드 강화
- [ ] **인증/권한**: `fastapi-users` 라이브러리 도입, JWT + SQLite 동작 후 Role 기반 데코레이터 적용.
- [ ] **WebSocket** 스트림: Chat LLM 실시간 토큰 전송 → `fastapi-sockette` 패턴 참고.

### 3-3. Security & Observability
- [ ] **Audit Log**: `structlog` → `loguru` + Grafana Loki handler.
- [ ] **Dependency Scanning**: `github/codeql-action` 추가.

### 3-4. Action/Function 엔진
- [ ] **Ontology Action** 모듈 스켈레톤 작성 → `celery` or `prefect flow.run_task()` 연동.
- [ ] **Rules 엔진**: `durable-rules` GitHub 프로젝트 벤치마크.

### 3-5. 테스트 / 품질
- [ ] **pytest coverage** 배지 >= 80%. 데이터 탐색기, Ontology API 단위·통합 테스트 보강.
- [ ] **LLM Evals**: `promptfoo` Git 예시 따라 `tests/llm_eval/` 스위트 작성.

---

## 4. 단계별 실행 계획 (6월 Sprint)

| 주차 | 목표 | 핵심 작업 | 산출물 |
|-----|------|---------|-------|
| **4주차** | 인증 & 보안 기반 구축 | fastapi-users 통합, Streamlit Session Auth Adaptor | PR #auth-backend, doc `AUTH.md` |
| **5주차** | RAG + Vector Store | Weaviate Docker Compose, LangChain `WeaviateRetriever` 랩퍼 | `rag_pipeline.py`, UI QA 탭 |
| **6주차** | ML 모델링 모듈화 | Sklearn pipeline 템플릿, MLFlow tracking 초기화 | `models/` 아키텍처, mlflow UI compose |
| **7주차** | Observability 강화 | Loki logging handler, Grafana dashboard json | `logging_conf.py`, dashboard import 파일 |
| **8주차** | Action 엔진 PoC | Prefect subflow → Ontology Action trigger | `actions/` 모듈, demo notebook |

---

## 5. 참조 GitHub 리소스

| 목적 | Repo | 핵심 포인트 |
|------|------|-----------|
| FastAPI Auth | github.com/fastapi-users/fastapi-users | JWT, Oauth, SQLite adapter |
| RAG 참고 | github.com/weaviate/weaviate
| | `examples/qa-with-langchain` | Vector store + LangChain 통합 |
| ML 파이프라인 템플릿 | github.com/drivendataorg/cookiecutter-data-science | 폴더 표준화, Makefile |
| Observability | grafana/loki-python | Python logging→Loki handler 샘플 |
| LLM Evals | github.com/promptfoo/promptfoo | YAML 기반 시나리오 테스트 |

---

## 6. 문서 갱신 및 향후 작업

 - 본 보고서를 `docs/reports/progress_report_2025-06-05.md` 로 버전관리.
- 위 개선 로드맵 진척 시 `README.md` Roadmap 섹션 업데이트.
- 스프린트 종료 시 `CHANGELOG.md` 추가.

---

## 보류 중인 중요 작업

### 1. 데이터베이스 마이그레이션 계획
- **현재 상태**: SQLite 사용 중
- **목표**: PostgreSQL로 마이그레이션
- **필요 작업**:
  - PostgreSQL 서버 설정
  - SQLAlchemy 모델 마이그레이션 스크립트 작성
  - 데이터 마이그레이션 테스트
  - 무중단 전환 계획 수립
- **고려사항**:
  - 기존 데이터 보존
  - 다운타임 최소화
  - 롤백 계획

### 2. SMTP 이메일 서비스 구성
- **현재 상태**: 이메일 기능 구현됨 (비활성)
- **필요 구성**:
  - SMTP 서버 선택 (Gmail/AWS SES/SendGrid 등)
  - 앱 비밀번호 또는 API 키 발급
  - 이메일 템플릿 디자인
  - 발송 제한 및 모니터링 설정
- **보안 고려사항**:
  - 이메일 인증 필수
  - 스팸 방지 정책 준수
  - 개인정보 보호 규정 준수

### 우선순위 및 일정
1. 데이터베이스 마이그레이션: 높음 (시스템 안정성)
2. SMTP 구성: 중간 (사용자 경험)

---

> **요약** : 현재 플랫폼은 **기능 72%** 수준으로 MVP 가치 입증에는 충분하나, 보안·RAG·전통 ML·Action 엔진 등이 여전히 미흡합니다. 위 우선순위 대로 8주 스프린트를 수행하면 Palantir AIP 준하는 기능 커버리지가 90% 이상으로 상승할 것입니다. 구체 작업은 상기 표를 참조해 issue / milestone으로 등록해 주시기 바랍니다. 