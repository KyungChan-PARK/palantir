# Changelog v5.1 (2025)

## 신규/강화 기능
- Self-Improve Loop: ruff, black, bandit, safety, radon, mutmut, pytest, benchmark, Prometheus 지표 자동화
- APScheduler nightly self-improve, /metrics/self_improve 노출
- weaviate/neo4j 실물 백업, 30일 롤링, Slack Webhook 알림
- fastapi-users JWT refresh 토큰 회전, slowapi Gold/Free tier rate-limit
- OWASP dependency-check CI 통합, 포트 충돌 선제 Kill, pytest 병렬
- changelog, deployment, grafana_setup, troubleshooting 문서화

## 품질 게이트
- 커버리지 ≥ 92 %, mutation 생존율 ≤ 30 %, 복잡도 최악 등급 ≤ C
- CI 녹색, error_report 없음

## 기타
- Grafana/Loki/Promtail docker-compose, Prometheus 연동
- logs/self_improve_YYYYMMDD.md, self_improve_metrics.prom 자동화 