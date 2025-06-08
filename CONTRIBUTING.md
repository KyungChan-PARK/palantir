# Contributing Guide

감사합니다! 본 프로젝트에 기여하시려면 아래 절차를 따라 주세요.

## 개발 환경 설정
1. **필수 요구사항**
   - Python 3.13
   - Node.js 18.x 이상 (UI 개발 시 필수)
   - Git
   - Visual Studio Code (권장)

2. **환경 설정**
   - Python 가상환경 생성 및 의존성 설치
   - Node.js 18.x 이상 설치 (nvm 사용 권장)
   - yarn 패키지 매니저 설치 (`npm install -g yarn`)

1. **Issue 생성**
   - 버그 신고 또는 기능 제안 시 GitHub Issue를 생성하고, 가능하면 재현 절차/스크린샷을 첨부합니다.
2. **PRD & RFC**
   - 큰 기능 추가 시 `docs/`에 PRD와 RFC 문서를 먼저 작성해 주세요.
3. **Fork & Branch**
   - `main` 브랜치를 기준으로 topic 브랜치를 만듭니다. 네이밍 예시: `feature/ask-parallelism`.
4. **코딩 규칙**
   - 코드는 `ruff`, `black` 포맷을 통과해야 하며 테스트 커버리지를 90% 이상 유지합니다.
5. **Commit 메시지**
   - [Conventional Commits](https://www.conventionalcommits.org/) 스타일을 권장합니다.
6. **Pull Request**
   - PR에는 변경 요약, 테스트 결과 스크린샷, 관련 Issue 링크를 포함합니다.
7. **CI 통과**
   - GitHub Actions CI가 통과되어야 병합됩니다.

## Windows 11 개발자 추가 팁
- PowerShell 실행 시 `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`를 통해 스크립트 실행을 허용하세요.
- `setup_codex_env.ps1`는 관리자 권한 PowerShell에서 실행하는 것을 권장합니다.
- Node.js 설치 시 nvm-windows 사용을 권장합니다. (https://github.com/coreybutler/nvm-windows)
- yarn 설치 후 `yarn config set registry https://registry.npmjs.org`로 레지스트리를 설정하세요. 