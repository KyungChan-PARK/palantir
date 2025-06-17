# Palantir AIP 운영/보안/정책 가이드 (POLICY.md)

## 1. 운영 환경 정책
- 반드시 WSL Ubuntu 환경에서만 실행 (PowerShell 금지)
- 모든 서비스(FastAPI, Streamlit, Prefect 등)는 WSL Ubuntu에서 구동
- 운영 자동화는 run_all.sh 스크립트 활용
- 정책/운영/보안 자동화는 .cursorrules 파일과 연동

## 2. .cursorrules 정책 예시
```
[allow]
pytest
flake8
mypy
git add
git commit
git push
git checkout
git branch
docker build
docker-compose up
docker-compose down

[deny]
rm -rf
git push --force
shutdown
reboot
:(){ :|:& };:
dd if=
mkfs
chmod 777 -R /
chown -R root
curl http://* | sh
wget http://* | sh

[policy]
# 테스트/린트/정적분석 명령은 항상 자동 실행 허용
# 3회 연속 실패 시 자동 중단 및 Planner 재계획
# 위험 명령(시스템 파괴, 강제 푸시 등)은 절대 차단
# 커밋/브랜치/빌드/테스트 등 개발 관련 명령은 허용
# 반복 실패/예외 발생 시 자동 알림 및 휴먼 세이프가드
```

## 3. 인증/권한/보안 정책
- JWT 기반 인증/권한 관리 적용 (API/대시보드/운영)
- 민감 정보(키, 토큰 등)는 환경변수 또는 secrets로 관리
- 외부 API/DB 연동 시 보안 정책 준수
- 정책 위반 시 즉시 차단 및 Slack/이메일 등으로 실시간 알림

## 4. 운영/모니터링/알림
- Prometheus, Grafana, docker-compose 등으로 상태/이벤트/로그 모니터링
- 주요 이벤트/에러/상태 변화/정책 위반은 Slack/이메일/대시보드 등으로 실시간 알림
- 운영 자동화(run_all.sh) 및 정책/보안/운영 이벤트는 실시간 대시보드와 연동

## 5. 실전 운영 수칙
- 운영 중단/재시작/배포는 반드시 WSL Ubuntu에서만 진행
- 위험 명령/정책 위반 시 즉시 알림 및 자동 차단
- 3회 연속 실패 시 자동 중단 및 Planner 재계획
- 운영 정책/보안 정책/FAQ/README/문서 최신화 필수 