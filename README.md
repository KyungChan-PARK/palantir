# Palantir-Inspired Local AI Ops Suite v5.1

## 🟢 운영 자동화 규칙
- **gpt-4.1 에이전트**가 설계·코드·테스트·배포·문서화·운영 자동화 전담
- 실패 시 logs/error_report_YYYYMMDD.md 기록, o3 패치 후 재시도
- self_improve.py: 매일 03:00 ruff/black/bandit/safety/radon/mutmut/pytest/benchmark 루프
- 품질 게이트: ruff 0.4, black 88, pytest-cov≥92%, mutation 생존율≤30%, 복잡도≤C
- LLM은 OpenAI API 단일 사용, 추가 정보 필요시 웹 리서치 자동

## 🏁 스프린트/스테이지별 자동화
| Stage | 산출물 | 완료 기준 |
|-------|--------|-----------|
| 0 | self_improve.py, 스캐폴딩 | /status skeleton 200 |
| 1 | FastAPI + /status, CI | CI 초록 |
| 2 | 파이프라인 UI+transpiler, 온톨로지 sync | YAML→Job 실행 |
| 3 | /ask+AutoGen, Zero-Trust | 자연어 SQL 작동 |
| 4 | 백업, Prometheus/Loki, Release | 헬스체크 OK/OK |
| 5 | Self-Improve Loop, 보안 강화 | 품질 게이트 통과 |

---

# Palantir 저코드 파이프라인 플랫폼 (2025)

## 개요
- Python 3.13 기반, OpenAI LLM, Neo4j, FastAPI, APScheduler, Prometheus, Zero-Trust 보안
- 저코드 파이프라인 빌더, 온톨로지 동기화, 자연어 코드 생성, CI, 백업, 관측, 감사 추적

## 주요 기능
- Drag&Drop UI ↔ YAML ↔ Python DAG 변환 및 실시간 검증
- ontology/*.yaml → Neo4j 동기화 (다중 hop)
- /ask: 자연어 → SQL/PySpark 코드 자동 생성 및 실행
- Zero-Trust(JWT, rate-limit, LRU 캐시)
- 주간 백업(weaviate, neo4j)
- Prometheus /metrics, Loki 로그(sidecar)
- CI: ruff, black, pytest-cov≥90%, artefact 업로드

## 설치 및 실행
### 시스템 요구사항
- Python 3.13
- Node.js 18.x 이상 (UI 개발 및 빌드용)
- OpenAI API Key (환경변수 OPENAI_API_KEY)
- Neo4j, Weaviate, Prometheus, Loki, Grafana (Docker 권장)
- SLACK_WEBHOOK_URL 환경변수(옵션)

### Online Mode
```bash
python install_dependencies.py
uvicorn main:app --reload
```

## 테스트
```bash
python -m pytest --cov=app --cov-fail-under=90
```

## 백업
- weaviate: `backups/weaviate_YYYYMMDD.snap`
- neo4j: `backups/neo4j_YYYYMMDD.dump`

## 보안
- JWT 인증(Authorization: Bearer) + refresh 토큰 회전
- Gold/Free tier rate-limit, LRU 128 캐시
- OWASP dependency-check CI 통합

## 관측
- Prometheus: `/metrics`, `/metrics/self_improve`
- Loki: sidecar 설정 예시
- Grafana 대시보드 자동화

```yaml
loki:
  image: grafana/loki:2.9.0
  ports:
    - "3100:3100"
  command: -config.file=/etc/loki/local-config.yaml
```

## 문서
- [docs/deployment.md](docs/deployment.md)
- [docs/troubleshooting.md](docs/troubleshooting.md)
- [docs/grafana_setup_win.md](docs/grafana_setup_win.md)
- [changelog_v5.1.md](changelog_v5.1.md)

## CI
- `.github/workflows/ci.yml` 자동화

## 버전
- v5.1 (2025)

## 📑 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
   1. [Online Mode](#online-mode)
   2. [Offline Mode (Air-gapped)](#offline-mode-air%E2%80%91gapped)
   3. [Windows 11 Setup Notes](#windows11-setup-notes)
4. [Usage Examples](#usage-examples)
5. [API Reference](docs/API_REFERENCE.md)
6. [Product Requirements](docs/FEATURE_PRD.md)
7. [AI Agent Rules](AI_AGENT_RULES.md)
8. [Contributing](CONTRIBUTING.md)

## Project Overview
본 프로젝트는 FastAPI 백엔드, Reflex 기반 UI, Weaviate 벡터 DB, Neo4j 그래프 DB를 통합하여 저코드 파이프라인 빌더와 자연어 질의 생성을 지원하는 **로컬 AI Ops 플랫폼**입니다. 오프라인(네트워크 차단) 환경 또는 일반 온라인 환경에서 동일한 코드를 실행할 수 있도록 설계되었습니다.

> **Why?** 팔란티어 AIP에서 영감을 받아, 온프레미스 환경에서도 데이터 파이프라인·LLM 서비스를 안전하게 운영할 수 있는 레퍼런스를 제공합니다. 