# Troubleshooting Guide

## 1. 포트 충돌
- 8000, 7687, 8080, 3100, 9090 등 이미 사용 중인지 확인
- 기존 프로세스 종료 후 재시도

## 2. 의존성 오류
- `python install_dependencies.py`로 재설치
- requirements.txt 버전 확인

## 3. 인증 오류(JWT)
- Authorization 헤더, 토큰 유효성 확인
- SECRET_KEY 일치 여부 확인

## 4. 커버리지 실패
- `pytest --cov=app --cov-fail-under=90`로 직접 확인
- 테스트 누락 코드 보강

## 5. 백업 미생성
- backups/ 디렉토리 권한 확인
- APScheduler 정상 동작 여부 확인

## 6. LLM/오픈AI 오류
- OPENAI_API_KEY 환경변수 확인
- 네트워크 연결 확인

## 7. Neo4j/Weaviate 연결 오류
- 서비스 기동 상태, 포트, 인증정보 확인

## 8. CI 실패
- 로그에서 실패 단계 확인 후 위 항목별 점검 