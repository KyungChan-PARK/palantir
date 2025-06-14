# Deployment Guide (v5.1)

## 1. 환경 준비
- Python 3.13
- OpenAI API Key (환경변수 OPENAI_API_KEY)
- Neo4j, Weaviate, Prometheus, Loki, Grafana (Docker 권장)
- SLACK_WEBHOOK_URL 환경변수(옵션)

## 2. 의존성 설치
```bash
python install_dependencies.py
```

## 3. 서비스 기동
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 4. Self-Improve 루프
- APScheduler로 매일 03:00 UTC 자동 실행
- logs/self_improve_YYYYMMDD.md, self_improve_metrics.prom 생성
- /metrics/self_improve Prometheus scrape

## 5. 백업
- weaviate client.backup.create, neo4j-admin backup, 30일 롤링, Slack Webhook 알림
- backups/YYYYMMDD/ 디렉토리 확인

## 6. 보안
- JWT refresh 토큰 회전, Gold/Free tier rate-limit

## 7. CI
- .github/workflows/ci.yml: 포트 선제 Kill, self_improve.py, dependency-check, 병렬 pytest, artefact 업로드

## 8. 모니터링
- Prometheus: /metrics, /metrics/self_improve
- Grafana: docs/grafana_setup_win.md 참고
- Loki/Promtail: docker-compose.loki.yaml 참고

## 9. 환경변수
- OPENAI_API_KEY: OpenAI API 키
- NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD (필요시)

## 10. 포트
- FastAPI: 8000
- Prometheus: 9090
- Loki: 3100
- Neo4j: 7687
- Weaviate: 8080

## 11. 모니터링
- Prometheus: `/metrics`
- Loki: sidecar 로그

## 12. 보안
- JWT 인증, rate-limit, LRU 캐시

## 13. CI
- GitHub Actions: `.github/workflows/ci.yml` 