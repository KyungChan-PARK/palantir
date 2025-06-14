# API Reference

모든 엔드포인트는 `/` 루트를 기준으로 합니다.

| Method | Path | 설명 | 인증 | Rate-Limit |
|--------|------|------|------|-----------|
| POST | /ask | 자연어 → SQL/PySpark 코드 생성 후 실행 | JWT (Bearer) | 5/min (기본) |
| POST | /pipeline/validate | 파이프라인 YAML 유효성 검증 | JWT (Bearer) | 5/min |
| POST | /pipeline/submit | 파이프라인 제출 및 스케줄링 | JWT (Bearer) | 5/min |
| POST | /ontology/sync | YAML 온톨로지 → Neo4j 동기화 | JWT (Bearer) | 관리자만 |
| GET  | /status | 앱 및 백엔드 서비스 헬스체크 | Public | N/A |
| GET  | /metrics | Prometheus 지표 노출 | Public | N/A |

## 요청/응답 예시

### POST /ask
```bash
curl -X POST http://localhost:8000/ask \
     -H "Authorization: Bearer <JWT>" \
     -H "Content-Type: application/json" \
     -d '{"query": "select all users", "mode": "sql"}'
```
응답:
```json
{
  "result": "[MOCK EXECUTE] sql: SELECT * FROM table WHERE text LIKE '%select all users%';",
  "code": "SELECT * FROM table WHERE text LIKE '%select all users%';"
}
```

### GET /status
```json
{
  "app": "ok",
  "weaviate": "ok",
  "neo4j": "ok",
  "self_improve": "ok"
}
```

> 자세한 파라미터와 응답 구조는 FastAPI 소스 및 `tests/` 디렉터리의 테스트 케이스를 참고하세요. 