# Product Requirements Document (PRD)

본 문서는 **Palantir-Inspired Local AI Ops Suite**의 핵심 기능과 요구사항을 개략적으로 기술합니다. 보다 상세한 설계는 각 Feature Spec / RFC 문서를 통해 이어집니다.

## 1. 목표 (Why)
- 온프레미스, 오프라인 환경에서도 데이터 파이프라인 자동화와 AI 코드 생성을 제공한다.
- 엔터프라이즈 품질(테스트 커버리지 90% 이상, 보안 게이트, 관측성)을 유지한다.
- AI 에이전트(예: Cursor GPT-4.1)가 안정적으로 코드를 읽고 변경할 수 있도록 충분한 컨텍스트를 문서화한다.

## 2. 핵심 기능 (What)
1. **Ask Query Generation**
   - 자연어 입력 → SQL 또는 PySpark 코드 생성
   - 결과 미리보기(모의 실행)
2. **Pipeline Orchestration**
   - YAML 파이프라인 정의 검증 및 스케줄링
   - DAG 시각화 지원(UI)
3. **Ontology Sync**
   - YAML 온톨로지 → Neo4j 그래프 업서트
4. **Backup & Self-Improve**
   - 주간 Weaviate/Neo4j 백업, 롤링 삭제
   - 매일 03:00 품질 개선 루프(ruff/black/pytest/Bandit)
5. **Observability & Security**
   - Prometheus `/metrics`, Loki 로그 사이드카
   - JWT 인증, Rate-Limit, LRU 캐시

## 3. 가치 (Value)
- 데이터 팀은 GUI 또는 YAML로 파이프라인을 빠르게 배포할 수 있음
- 오프라인 시설에서도 LLM-기반 코드 생성을 활용 가능
- 자동 백업 및 품질 개선으로 운영 리스크 감소

## 4. 성공 지표 (KPIs)
| Metric | Target |
|--------|--------|
| API 가용성 | ≥ 99% |
| `/ask` 평균 지연 | ≤ 300 ms (모의 실행 기준) |
| 테스트 커버리지 | ≥ 90% |
| 린트/포맷 오류 | 0 |
| 백업 보존 기간 | ≥ 30 일 |

## 5. 범위 제외 (Out of Scope)
- 실시간 데이터 스트리밍 처리 (향후 Roadmap)
- ML 모델 서빙 (향후 Roadmap)

## 6. 일정 (Milestones)
| Stage | 목표 | 완료 기준 |
|-------|------|-----------|
| 0 | 스캐폴딩 & Self-Improve | `/status` skeleton 200 |
| 1 | FastAPI MVP & CI | CI 초록, `/metrics` OK |
| 2 | UI + Pipeline 엔진 | YAML→DAG 실행 OK |
| 3 | 자연어 SQL | `/ask` 반환 SQL 검증 OK |
| 4 | 백업 & Release | 헬스체크 OK/OK |

## 7. 리스크 및 완화책
- **LLM 의존성**: 오프라인 모드에서 로컬 모델로 대체할 수 있도록 설계
- **Windows 호환성**: 설치 스크립트 개선 및 테스트 자동화
- **AI 코드 오용**: 정책 가드(verify_jwt, rate-limit) 및 코드 검증 테스트 강화 