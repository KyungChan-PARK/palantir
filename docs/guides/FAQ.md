# Palantir AIP FAQ

## 1. WSL Ubuntu 환경 관련

**Q. PowerShell에서 실행해도 되나요?**
A. 아니요. 반드시 WSL Ubuntu 환경에서만 실행해야 하며, PowerShell은 금지입니다.

**Q. 의존성 설치가 안 되거나, 패키지 충돌이 발생합니다.**
A. `pip install -r requirements.txt`를 WSL Ubuntu에서 실행하세요. Python 3.9 이상 권장.

## 2. API/대시보드/ETL 연동

**Q. FastAPI/Streamlit/Prefect가 제대로 실행되지 않습니다.**
A. `run_all.sh` 스크립트로 한 번에 실행하거나, 각 서비스를 개별적으로 실행하세요. 로그 파일(fastapi.log 등)에서 에러를 확인하세요.

**Q. 대시보드에서 실시간 데이터가 안 보입니다.**
A. FastAPI 서버가 정상적으로 실행 중인지 확인하고, API URL(`http://localhost:8000/ontology`)이 올바른지 점검하세요.

## 3. 보안/정책/운영 자동화

**Q. 위험 명령어가 실행될 수 있나요?**
A. .cursorrules 정책에 따라 `rm -rf`, `git push --force` 등 위험 명령은 차단됩니다. 3회 연속 실패 시 자동 중단 및 Planner가 재계획합니다. 정책 위반 시 즉시 차단 및 Slack/이메일 등으로 알림이 전송됩니다.

**Q. 인증/권한 관리는 어떻게 하나요?**
A. JWT 기반 인증/권한 관리가 적용되어 있습니다. 운영 정책은 `../references/POLICY.md`를 참고하세요.

**Q. 운영 자동화/모니터링은 어떻게 하나요?**
A. run_all.sh로 FastAPI, Streamlit, Prefect를 한 번에 실행할 수 있습니다. Prometheus, Grafana, docker-compose 등으로 상태/이벤트/로그를 모니터링하며, 주요 이벤트/정책 위반은 실시간 대시보드 및 알림으로 연동됩니다.

## 4. 확장/테스트/운영

**Q. 새로운 온톨로지 객체/관계를 추가하고 싶어요.**
A. `palantir/ontology/objects.py`와 API, 대시보드 코드를 확장하면 됩니다.

**Q. 통합 테스트는 어떻게 하나요?**
A. `pytest -v`로 전체 테스트를 실행할 수 있습니다. Prefect Flow, API, 대시보드, ETL/ML, 관계/이벤트 생성 등도 자동화 테스트에 포함됩니다.

## 5. 기타

**Q. 실전 활용/운영/확장/테스트/보안/정책 등 더 자세한 가이드는 어디서 볼 수 있나요?**
A. README, AGENTS.md, ai_agent_self_improvement.md, `../references/POLICY.md`, `USAGE_EXAMPLES.md`, CONTRIBUTING.md, docs/ 폴더를 참고하세요
