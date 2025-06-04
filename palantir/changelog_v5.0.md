# Changelog v5.0 (2025)

## 신규 기능
- 저코드 파이프라인 빌더 (Drag&Drop UI ↔ YAML ↔ Python DAG)
- 온톨로지 멀티-계층 모델 & Neo4j 동기화
- 자연어 /ask (GPT-4 function_call → SQL/PySpark)
- Zero-Trust(JWT, rate-limit, LRU 캐시)
- 주간 백업(weaviate, neo4j)
- Prometheus /metrics, Loki 로그(sidecar)
- CI: ruff, black, pytest-cov≥90%, artefact 업로드
- self_improve.py: 자동 코드/문서 개선 루프

## 품질 게이트
- ruff 0.4, black 88, pytest-cov≥90%, CI 헬스체크(`/status`, `/metrics`)

## 기타
- 운영/배포/트러블슈팅/릴리즈 문서화
- GitHub Release v5.0 