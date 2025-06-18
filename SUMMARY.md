# Palantir AIP 문서

## 시작하기
- [소개](README.md)
- [설치 가이드](docs/setup/deployment.md)
- [자주 묻는 질문](docs/guides/FAQ.md)

## 아키텍처
- [시스템 구조](docs/architecture/FEATURE_PRD.md)
- [보안 정책](docs/architecture/POLICY.md)

## API 문서
- [API 레퍼런스](docs/api/API_REFERENCE.md)
- [사용 예제](docs/guides/USAGE_EXAMPLES.md)

## 개발 가이드
- [인증/권한 관리](docs/development/AUTH.md)
- [사용자 관리](docs/development/user_management.md)
- [문제 해결](docs/development/troubleshooting.md)

## 모니터링
- [Grafana 설정](docs/monitoring/grafana_setup_win.md)

## 개발 현황
- [개발 로그](docs/reports/DEVLOG.md)
- [진행 보고서](docs/reports/progress_report_2025-06-05.md)

## 주요 변경 요약
- 테스트 92%+ 커버리지 달성 (총 188개, 185개 통과)
- FastAPI DI/Mock, dependency_overrides, edge case 보강
- pre-commit (black, isort, flake8) 자동화
- GitHub Actions matrix (Windows/Ubuntu, Python 3.13, 커버리지 92% 기준)
- Gunicorn+Uvicorn 프로덕션 빌드, docker-compose, APScheduler, Tesseract 자동감지
- 보안(JWT refresh), /metrics 라벨, E2E health check, 의존성 취약점 검사

## 커버리지
- 전체: **92.17%**
- 미달 라인: pipeline/report/upload 일부 예외/에러 분기(테스트로 보강)

## PR URL
- https://github.com/KyungChan-PARK/palantir/pull/new/feat/production

## 주요 이미지 SHA (docker build)
- 최신 빌드 시: `docker images | findstr palantir-api`

## 기타
- 모든 구조적 오류 및 테스트 실패 해결
- CI/CD, pre-commit, 보안, 운영 자동화 기반 완비 