# Palantir AIP - 자가개선형 멀티에이전트 오케스트레이션 플랫폼

## 개요
- **멀티에이전트 오케스트레이션**: Planner/Developer/Reviewer/SelfImprover 등 역할별 에이전트가 자동 협업하며, Reviewer→SelfImprover→Reviewer 루프, 3회 실패 시 Planner 재계획, 상태 기반 분기/이력/알림/정책/Slack 연동까지 지원
- **MCP 계층**: LLM, 파일, Git, 테스트, 웹 등 도구를 안전하게 추상화하며, 테스트 자동화(테스트+린트+정적분석+보안+복잡도+뮤테이션 등)와 정책/가드레일/알림(위험 명령/반복 실패/정책 위반 시 Slack 등 알림) 내장
- **자가개선 루프**: 코드 분석→개선안→적용→테스트→롤백/이력관리까지 자동화, 상태/이력/반복/알림/정책/Slack 연동
- **온톨로지/ETL/ML/임베딩/DB/대시보드/API/문서화**: 실전 데이터/AI/운영/시각화/문서화까지 통합, 온톨로지 객체/관계/유효성/추천/분석/이벤트/상태/실시간 연동 지원
- **테스트/운영/보안/CI/CD**: pytest, pre-commit, GitHub Actions, docker-compose, Prometheus/Grafana, JWT 등 실전 인프라 적용, .cursorrules 정책/가드레일/알림 내장

## 정책/환경
- **반드시 WSL Ubuntu 환경에서 실행** (PowerShell 금지)
- **위험 명령 차단/정책/가드레일/알림**: .cursorrules 정책 적용, 반복 실패/정책 위반/위험 명령 시 자동 중단 및 Slack 등 알림

## 주요 폴더 구조
```
palantir/
  core/           # 에이전트, 오케스트레이터, 공통 추상화
  services/mcp/   # LLM, 파일, Git, 테스트, 웹 MCP 계층
  api/            # FastAPI 엔드포인트 (추천/분석/이벤트/상태 등 실전 API)
  models/         # LLM/임베딩/AI 계층
  ontology/       # 온톨로지/지식그래프 (객체/관계/유효성/추천/분석/이벤트)
  process/        # 워크플로우/ETL/ML/임베딩 (실전 파이프라인)
  ui/             # Streamlit 대시보드 (실시간 상태/추천/분석/이벤트/알림)
  tests/          # 단위/통합/보안/성능/자동화 테스트
```

## 통합 실행/운영 예시 (WSL Ubuntu)
```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. FastAPI 서버 실행
uvicorn palantir.api.main:app --reload --host 0.0.0.0 --port 8000

# 3. Streamlit 대시보드 실행
streamlit run palantir/ui/app.py

# 4. Prefect ETL/ML 파이프라인 실행
python -m palantir.process.flows
```

## 주요 실전 API/엔드포인트 예시
- `/ontology/recommend_products/{customer_id}`: 고객별 추천 상품
- `/ontology/order_timeline/{order_id}`: 주문별 이벤트 타임라인
- `/ontology/similar_products/{product_id}`: 유사 상품 추천
- `/ontology/alerts`: 실시간 알림/상태
- `/ontology/graph`: 온톨로지 네트워크/관계 그래프

## 대시보드/자동화 루프/실시간 연동
- Streamlit 대시보드: 에이전트 상태, 테스트 결과, 온톨로지 객체/관계/추천/분석/이벤트/실시간 알림 등 시각화
- 자가개선 루프: 코드 분석→개선안→적용→테스트→롤백/이력관리, 반복 실패/정책 위반/위험 명령 시 자동 중단 및 Slack 등 알림
- ETL/ML/임베딩 파이프라인: 데이터 적재→임베딩 생성→ChromaDB 적재→ML 실험→온톨로지/이벤트 기록, 실시간 객체/관계/임베딩 자동 갱신

## 테스트/운영 자동화
```bash
pytest -v
```
- tests/test_agents.py: 에이전트/오케스트레이터 단위 테스트(LLM 모킹)
- Prefect Flow, API, 대시보드, ETL/ML, 관계/이벤트 생성 등 통합 테스트
- MCP/테스트 자동화(테스트+린트+정적분석+보안+복잡도+뮤테이션 등)

## 모니터링/운영 자동화
- Prometheus, Grafana, docker-compose, 로그/이벤트/상태 모니터링 등 운영 자동화
- 운영 정책, .cursorrules, JWT 인증/권한, 보안/정책/FAQ 등 참고
- Slack 등 실시간 알림 연동

## 확장/커스터마이징/문서
- MCP/온톨로지/에이전트/오케스트레이터/대시보드/정책 등 자유롭게 확장
- 주요 문서: AGENTS.md, ai_agent_self_improvement.md, ai_aigent_orchestration.md, 개발상황.md 등 참고
- 기여 가이드: CONTRIBUTING.md, .github/ 폴더 참고

## FAQ/참고
- 실전 활용/운영/확장/테스트/보안/정책 등 FAQ 및 주요 가이드 docs/ 폴더 참고
- 자세한 설계/로드맵/지침은 AGENTS.md, ai_agent_self_improvement.md 등 문서 참고
