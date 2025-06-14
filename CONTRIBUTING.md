# Contributing Guide

감사합니다! 본 프로젝트에 기여하시려면 아래 절차를 따라 주세요.

1. **WSL Ubuntu 환경 필수**
   - 모든 개발/운영/테스트/자동화는 반드시 WSL Ubuntu 환경에서 진행해야 합니다. PowerShell은 금지입니다.
2. **정책/보안/운영 준수**
   - .cursorrules, POLICY.md, FAQ.md, README.md 등 정책/보안/운영 문서를 반드시 숙지하고 준수해 주세요.
3. **Issue 생성**
   - 버그 신고 또는 기능 제안 시 GitHub Issue를 생성하고, 가능하면 재현 절차/스크린샷을 첨부합니다.
4. **PRD & RFC**
   - 큰 기능 추가 시 `docs/`에 PRD와 RFC 문서를 먼저 작성해 주세요.
5. **Fork & Branch**
   - `main` 브랜치를 기준으로 topic 브랜치를 만듭니다. 네이밍 예시: `feature/ask-parallelism`.
6. **코딩 규칙/테스트/자동화**
   - 코드는 `ruff`, `black` 포맷을 통과해야 하며 테스트 커버리지를 90% 이상 유지합니다.
   - `pytest -v`로 통합 테스트를 실행하고, Prefect Flow, API, 대시보드, ETL/ML, 관계/이벤트 생성 등 자동화 테스트를 포함합니다.
7. **Commit 메시지**
   - [Conventional Commits](https://www.conventionalcommits.org/) 스타일을 권장합니다.
8. **Pull Request**
   - PR에는 변경 요약, 테스트 결과 스크린샷, 관련 Issue 링크를 포함합니다.
9. **CI 통과**
   - GitHub Actions CI가 통과되어야 병합됩니다.
10. **문서/실전 예시/FAQ/정책 참고**
    - AGENTS.md, ai_agent_self_improvement.md, USAGE_EXAMPLES.md, FAQ.md, POLICY.md, README.md, docs/ 폴더의 실전 예시/정책/운영 가이드를 참고해 주세요.

## Windows 11 개발자 추가 팁
- PowerShell 실행 시 `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`를 통해 스크립트 실행을 허용하세요.
- `setup_codex_env.ps1`는 관리자 권한 PowerShell에서 실행하는 것을 권장합니다. 