# Palantir-Inspired Local AI Ops Suite v5.0

## 🟢 운영 자동화 규칙
- **gpt-4.1 에이전트**가 설계·코드·테스트·배포·문서화·운영 자동화 전담
- 실패 시 logs/error_report_YYYYMMDD.md 기록, o3 패치 후 재시도
- self_improve.py: 매일 03:00 ruff/black/pytest/Sphinx 루프, 개선점 기록
- 품질 게이트: ruff 0.4, black 88, pytest-cov≥90%, CI 헬스체크(`/status`, `/metrics`)
- LLM은 OpenAI API 단일 사용, 추가 정보 필요시 웹 리서치 자동

## 🏁 스프린트/스테이지별 자동화
| Stage | 산출물 | 완료 기준 |
|-------|--------|-----------|
| 0 | self_improve.py, 스캐폴딩 | /status skeleton 200 |
| 1 | FastAPI + /status, CI | CI 초록 |
| 2 | 파이프라인 UI+transpiler, 온톨로지 sync | YAML→Job 실행 |
| 3 | /ask+AutoGen, Zero-Trust | 자연어 SQL 작동 |
| 4 | 백업, Prometheus/Loki, Release | 헬스체크 OK/OK |

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
- JWT 인증(Authorization: Bearer)
- 5/min rate-limit, LRU 128 캐시

## 관측
- Prometheus: `/metrics`
- Loki: sidecar 설정 예시

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
- [changelog_v5.0.md](changelog_v5.0.md)

## CI
- `.github/workflows/ci.yml` 자동화

## 버전
- v5.0 (2025) 