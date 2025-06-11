# Palantir AI Platform – Developer Guide

> Single Source of Truth for all contributors (updated 2025-06-08)

---

## 1. 프로젝트 개요 (Project Vision)
본 프로젝트는 Palantir Foundry / AIP 철학을 오픈소스 스택으로 재현하여, 온톨로지 기반 데이터 통합·실시간 파이프라인·AI 어시스트 기능을 단일 플랫폼에 제공합니다.

핵심 지향점
1. 하이브리드 저코드 + SDK 개발 모델
2. 온톨로지-중심 객체 / 링크 / 액션 패러다임
3. Kafka → Pipeline → VectorStore → LLM 실시간 루프
4. Self-Improving LoRA 미세조정 루프
5. 엔터프라이즈-급 DevOps & Observability

---
## 2. 시스템 아키텍처 (System Architecture)
아래 다이어그램은 `docker-compose.yml` 을 기반으로 **자동 생성**됩니다.

![System Architecture](./assets/system_architecture.png)

**자동 생성 방법:**
- `poetry run python scripts/generate_architecture_diagram.py` 명령을 실행하면 최신 docker-compose.yml을 파싱하여 다이어그램을 `docs/assets/system_architecture.png`로 생성합니다.
- CI/CD 파이프라인에서도 자동으로 실행되어, 다이어그램이 항상 최신 상태로 유지됩니다.

구성요소 요약
| Stack | 역할 |
|-------|------|
| FastAPI `api` | REST + WebSocket 백엔드 / LLM 라우팅 |
| Kafka & Zookeeper | 실시간 이벤트 버스 (비동기 이벤트 스트림 및 데이터 수집) |
| PostgreSQL / SQLite | 메인 트랜잭션 DB |
| Weaviate | Vector Store (RAG) |
| Prometheus / Grafana | 모니터링 & 대시보드 |
| Loki | 로그 집계 |

---
## 3. 개발 & 배포
### 3.1 로컬 개발 환경 설정
```bash
# 의존성 설치 (Poetry)
poetry install --no-interaction --with dev
# 서비스 기동 (DB·Kafka·Grafana·Zookeeper 등)
docker-compose up -d
# 백엔드 	
poetry run uvicorn main:app --reload
# Reflex UI 예시
poetry run reflex run --app apps.reflex_ui.pipeline_ui.pipeline_ui:app
```
> Kafka와 Zookeeper는 docker-compose.yml에 정의되어 있으며, 위 명령으로 함께 실행됩니다.

### 3.2 프로덕션 배포
1. `docker-compose -f docker-compose.yml --profile prod up -d`  
2. Grafana → Import Dashboard json  
3. GitHub Actions 빌드된 Docker 이미지 `palantir:latest` 사용

---
## 4. 핵심 기능 & 코드 구조
| 기능 | 주요 모듈 |
|------|-----------|
| 실시간 스트리밍 → 파이프라인 | `palantir.ingest.kafka_consumer` → `palantir.core.pipeline` |
| 파이프라인 빌더 UI | `apps/reflex_ui/pipeline_ui/...` |
| LLM Ask / Feedback | `palantir/api/ask.py`, `palantir/core/llm_manager.py` |
| Self-Improve Loop | `scripts/run_finetuning.py`, `self_improve.py` |

---
## 5. UI 애플리케이션 (Presentation Layer)
| 디렉터리 | 프레임워크 | 상태 |
|-----------|-----------|------|
| `archive/streamlit_ui` | Streamlit | Deprecated – 초기 프로토타입, 아카이브됨 |
| `apps/reflex_ui` | Reflex + React-Flow | Main – 파이프라인 Builder, 대시보드 |

## 5.1 Reflex UI vs. Streamlit UI
현재 **apps/reflex_ui** 가 차세대 파이프라인 빌더·대시보드 기능을 제공하는 메인 UI입니다.  
`archive/streamlit_ui` 는 레거시 챗/데이터 탐색 인터페이스로 아카이브되어 있으며, 신규 기능은 Reflex UI에 먼저 반영됩니다.

실행 방법:
```bash
# Reflex UI (권장)
poetry run reflex run --app apps.reflex_ui.pipeline_ui.pipeline_ui:app

# 기존 Streamlit UI (아카이브, deprecated)
poetry run streamlit run archive/streamlit_ui/main.py
```

---
## 5.2 Kafka Ingestion Flow
`palantir.ingest.kafka_consumer.consume_messages` 가 Kafka 토픽 **raw-data-stream** 을 구독하여 실시간 JSON 이벤트를 파이프라인으로 전달합니다.

설정 값은 `docker-compose.yml` 의 `kafka` 서비스와 일치해야 하며, 토픽/브로커는 `palantir/core/settings.py` 에서 오버라이드할 수 있습니다.

---
## 5.3 Self-Improve Loop
`self_improve.py` 는 매일 03:00(WSL Cron) 품질 게이트(ruff/black/pytest/benchmark 등)를 실행하고 실패 시 `logs/error_report_*.md` 를 생성합니다.

파이프라인:
1. **테스트 & 린트** – 코드베이스 일관성 확보
2. **Radon, Mutmut** – 복잡도·뮤테이션 테스트 메트릭 수집
3. **Prometheus Export** – `/metrics/self_improve` 로 결과 노출

실행: `poetry run python self_improve.py`

---
## 6. API 명세 (API Reference)
FastAPI OpenAPI 스펙은 런타임에 `/openapi.json` 으로 제공됩니다.  
주요 엔드포인트 요약:
* `GET /status` – 헬스체크
* `POST /ask` / `POST /ask/feedback`
* `POST /pipeline/{validate|submit|visual}`

자세한 필드 설명은 Swagger UI (http://localhost:8000/docs) 참고.

---
## 7. 운영 & 모니터링 (Operations)
* Grafana 로그인 : `admin / $GRAFANA_ADMIN_PASSWORD`  
* 주요 대시보드 : API Latency, Kafka Lag, Self-Improve Metrics
* 문제 해결 Cheat-Sheet : `docs/troubleshooting.md` 내용 통합
  * 포트 충돌 → `docker ps` 후 컨테이너 정리
  * JWT 오류 → `users` 테이블 확인

---
## 8. 기여하기 (Contributing)
1. **브랜치 전략** : main (protected) / feat-/fix- 토픽 브랜치
2. **Lint & Test** : `make wsl-check && poetry run pytest -q`  \
   (Linux/WSL 환경과 Python 버전을 확인하는 스크립트)
3. **커밋 규칙** : Conventional Commits (`feat:`, `fix:` …)
4. **PR 체크리스트** : Test OK · CI green · 문서 업데이트

---
## 9. 유용한 스크립트 (Automation Scripts)
| 스크립트 | 설명 | 예시 |
|-----------|------|------|
| `scripts/run_finetuning.py` | 긍정 피드백(`llm_feedback`) 데이터로 LoRA 미세조정 실행 | `poetry run python scripts/run_finetuning.py` |
| `scripts/generate_architecture_diagram.py` | docker-compose.yml 파싱 → `docs/assets/system_architecture.png` 생성 | CI 워크플로에서 자동 호출 |
| `scripts/update_ci.py` | GitHub Actions 워크플로 파일을 코드에서 업데이트 | `python scripts/update_ci.py` |
| `scripts/gen_missing_tests.py` | 누락된 테스트 스텁 자동 생성 | `python scripts/gen_missing_tests.py palantir/` |

> 모든 스크립트는 `poetry run` 컨텍스트에서 실행할 것을 권장합니다.

---
## 중앙 집중식 로깅 및 관찰성 가이드 (Loki + loguru + correlation-id)

### 구조 및 연동 방식
- loguru + loguru-handler-loki로 모든 로그를 Loki로 전송 (JSON 직렬화)
- asgi-correlation-id 미들웨어로 모든 요청에 X-Correlation-ID 부여, loguru 컨텍스트에 자동 포함
- 표준 logging, warnings, print까지 loguru로 통합 리디렉션(InterceptHandler, warnings.showwarning 패치)
- 환경변수 LOKI_URL로 Loki 엔드포인트 지정(기본: http://loki:3100/loki/api/v1/push)

### 사용 예시
```python
from loguru import logger
logger.info("이벤트 발생", extra={"user_id": 123})
```
- FastAPI 엔드포인트/비즈니스 로직/예외/테스트 등 모든 곳에서 logger 사용
- print(), logging.info(), warnings.warn() 등도 자동 loguru로 전환됨

### 운영 및 모니터링
- Grafana(기본 http://localhost:3000) → Explore → Loki 데이터소스 선택
- LogQL 예시: `{app="palantir-api"}`
- 특정 요청 추적: `{app="palantir-api", correlation_id="..."}`
- 로그 필드(레벨, 타임스탬프, correlation_id, 사용자 정의 extra 등)로 필터링/분석

### 참고/운영 팁
- logger.add(sys.stderr, serialize=True)로 콘솔에서도 JSON 로그 확인 가능
- Loki 장애/미수신 시에도 콘솔 로그로 fallback
- 민감정보/PII는 extra에 포함하지 않도록 주의
- 로그 포맷/레벨/필드 등은 palantir/core/logging_config.py에서 일괄 관리

### Loki/Grafana에서 correlation_id별 로그 추적 테스트

- tests/test_logging_loki.py의 /log-test 엔드포인트를 호출하면 logger.info로 샘플 로그가 기록되고, 응답에 correlation_id가 포함됨
- Grafana Loki(Explore)에서 다음과 같이 쿼리:
  - `{app="palantir-api", correlation_id="응답에서 받은 값"}`
- 실제 로그 메시지, 레벨, 타임스탬프, extra 필드(testcase 등)까지 확인 가능

### 실전 장애 대응 및 트러블슈팅 가이드

- 장애 발생 시(예: 500 에러, 성능 저하, 비정상 동작 등) 아래 절차로 원인 추적

1. **문제 발생 시점/사용자/요청 정보 확보**
   - API 응답의 correlation_id, 사용자 ID, 타임스탬프 등 확보
2. **Grafana Loki에서 LogQL로 추적**
   - 예시: `{app="palantir-api", correlation_id="..."}`
   - 또는 `{user_id="..."}` 등 extra 필드로 필터링
3. **로그 상세 분석**
   - logger.info/debug/warning/error/exception 등 레벨별 로그 확인
   - extra 필드(요청 파라미터, 내부 상태, 예외 메시지 등)로 맥락 파악
   - warnings, 표준 logging, print까지 모두 loguru로 통합되어 있어 누락 없음
4. **장애 유형별 대응 예시**
   - 500 에러: logger.exception 로그에서 스택트레이스, 입력값, 내부 상태 확인
   - 성능 저하: 요청별 duration, 처리 단계별 로그 타임스탬프 비교
   - 외부 서비스 장애: logger.error/warning 메시지에서 외부 API/DB 호출 실패 여부 확인
5. **운영 팁**
   - Loki 장애 시에도 콘솔 로그(serialize=True)로 임시 추적 가능
   - 민감정보/PII는 extra에 포함하지 않도록 주의(필요시 마스킹)
   - 로그 필드/포맷/레벨 등은 palantir/core/logging_config.py에서 일괄 관리

### 민감정보(PII) 자동 마스킹 기능

- logger.info(..., extra={"email": "user@example.com", "password": "1234"}) 등으로 로그를 남길 때, extra에 포함된 email, password, ssn, phone, token 등 민감 필드는 자동으로 ***MASKED*** 처리됨
- 마스킹 대상 키는 palantir/core/logging_config.py의 SENSITIVE_KEYS에서 관리(필요시 확장/수정)
- 운영 팁: 민감정보가 extra에 포함되지 않도록 설계하는 것이 원칙이나, 불가피할 경우 자동 마스킹으로 2차 보호
- Loki/Grafana에서 마스킹된 로그는 "***MASKED***"로 표시됨

### 실시간 장애/에러 슬랙 알림 연동

- SLACK_WEBHOOK_URL 환경변수에 슬랙 인커밍 Webhook URL을 지정하면, logger.error/exception 발생 시 자동으로 슬랙 채널로 알림 전송
- 메시지에는 레벨, 본문, extra(상황 정보)가 포함됨
- 운영 팁: 장애/에러 발생 시 실시간 대응, 로그와 슬랙 알림을 연계해 신속한 원인 파악 가능
- 보안 주의: Webhook URL은 외부에 노출되지 않도록 .env, CI/CD secrets 등 안전하게 관리

### Sentry 연동(옵션)

- SENTRY_DSN 환경변수에 Sentry DSN을 지정하면 logger.error/exception 발생 시 자동으로 Sentry로 에러가 전송됨
- 슬랙 알림과 병행 동작 가능(중복 알림 방지 정책은 Sentry/슬랙 설정에서 조정)
- 운영 팁: 장애/에러 발생 시 Sentry 대시보드에서 스택트레이스, 컨텍스트, 발생 빈도 등 심층 분석 가능
- 보안 주의: SENTRY_DSN은 외부에 노출되지 않도록 .env, CI/CD secrets 등 안전하게 관리

### 알림/모니터링 정책 커스터마이징 및 운영 자동화 팁

- loguru logger.add()의 level, filter, patch, sink 옵션을 활용해 레벨별/필드별/조건부 알림 정책을 자유롭게 커스터마이즈 가능
- 예시: 특정 서비스/모듈/사용자/상황(extra 필드)에서만 슬랙/Sentry 알림을 보내고 싶을 때
  ```python
  def custom_slack_notify(message):
      if message.record["level"].name == "ERROR" and message.record["extra"].get("service") == "critical":
          # ...슬랙 전송...
  logger.add(custom_slack_notify, level="ERROR")
  ```
- 운영 자동화: 장애 발생 시 슬랙/이메일/전화/SMS 등 다양한 채널로 연동 가능(추가 sink 함수 작성)
- Loki/Grafana의 Alerting 기능과 연계해 임계치 기반 대시보드/알림도 구현 가능
- 실전 예시: 특정 사용자(user_id), 특정 API, 특정 에러코드, 트래픽 급증 등 다양한 조건에 따라 알림/모니터링 정책을 세분화하여 운영
- 정책 변경/테스트 후 반드시 실제 장애/에러 상황에서 알림이 정상 동작하는지 검증할 것

---
## [2025-06-11 기준] 최신 개발환경 및 운영 가이드

### 1. WSL2/Ubuntu 환경 강력 권장
- PowerShell/Windows 환경에서는 일부 명령어(예: rm, find, &&, docker 등)가 정상 동작하지 않으므로, 반드시 WSL2 Ubuntu 환경에서 개발/운영할 것.
- 프로젝트 폴더로 이동: `cd /mnt/c/palantir`

### 2. 가상환경 및 의존성 관리
- Python 3.12 기반 venv + pip 사용 권장
- requirements.txt(프로덕션), requirements-dev.txt(개발/테스트) 분리 관리
- 설치 예시:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. 불필요 파일/캐시/DB/로그/가상환경 정리 및 용량 최적화
- 아래 명령어로 모든 캐시/임시/DB/로그/가상환경 파일 완전 삭제:
```bash
rm -rf .venv __pycache__ .pytest_cache .mypy_cache .coverage .hypothesis .cache
find . -name '*.pyc' -delete
find . -name '*.pyo' -delete
find . -name '*.db' -delete
find . -name '*.log' -delete
sudo rm -rf ./data/postgres
```
- PowerShell에서는 동작하지 않으니 반드시 WSL2 Ubuntu에서 실행

### 4. 도커/서비스 실행 및 빌드
- buildx 미설치 시 `docker buildx install`로 설치
- docker-compose로 모든 서비스 실행: `docker-compose up -d --build`
- 환경변수 미설정 시 경고 발생(SECRET_KEY, GRAFANA_ADMIN_PASSWORD 등)
- 컨테이너 상태 확인: `docker ps`

### 5. DB 마이그레이션/테스트/서버 실행/검증
- Alembic 마이그레이션: `alembic upgrade head`
- 전체 테스트: `pytest`
- FastAPI 서버: `uvicorn main:app --host 0.0.0.0 --port 8000`
- 상태 확인: `curl http://localhost:8000/api/status` → {"status":"ok"}

### 6. 의존성/버전 이슈 및 해결법
- passlib, promptfoo 등 PyPI 버전 불일치 시 requirements 파일에서 최신/지원 버전으로 수정
- encountered 이슈 및 해결법, 환경변수, 권한 문제 등 실전 팁 추가

### 7. 문서 자동화 및 최신화
- scripts/generate_architecture_diagram.py로 아키텍처 다이어그램 자동 생성
- mkdocs, API 문서 자동화 등 최신화

---
> Generated by AI Agent – Docs as Code 