# Palantir AIP - 실전 운영/테스트/문서화/보안 자동화 가이드

## 폴더 트리
```
palantir/
├── .codex-config.json
├── requirements.txt
├── pipeline_ui/
│   └── requirements.txt
├── offline_preparation/
│   ├── python_packages/
│   │   └── unified/
│   │       ├── fastapi-0.115.12-py3-none-any.whl
│   │       ├── ...
│   ├── download_all_packages.ps1
│   ├── README.md
│   └── install_test.log
├── setup_codex_env.ps1
├── setup_codex_env.bat
└── OFFLINE_ENV_README.md
```

## 설치 방법
1. **오프라인 패키지 폴더(`offline_preparation/python_packages/unified/`)**에 모든 `.whl`/`.tar.gz` 파일이 들어있는지 확인
2. PowerShell에서 `setup_codex_env.ps1` 실행  
   (또는 CMD에서 `setup_codex_env.bat` 실행)
3. 자동으로 가상환경 생성, 패키지 설치, Codex 설정, 테스트까지 진행됨

## Codex 실행 예시
```powershell
& .venv\Scripts\activate
codex --auto-edit
```

## FAQ
- **패키지 설치 실패:**  
  → `offline_preparation/python_packages/unified/` 폴더가 비어있지 않은지 확인  
- **import 오류:**  
  → PYTHONPATH가 현재 폴더로 잡혀 있는지 확인  
- **테스트 실패:**  
  → `offline_preparation/install_test.log`에서 에러 메시지 확인

## 스크린샷 안내
- 설치 성공/실패, Codex 실행 화면 등 캡처하여 첨부

## 1. 폴더 트리 및 구성 설명

```
C:\palantir\
├── offline_preparation\
│   ├── python_packages\
│   │   ├── main_app_packages\
│   │   └── pipeline_ui_packages\
│   │   └── unified\
│   │   └── ... (모델 파일, MODEL_MANIFEST.json)
│   └── ...
├── setup_codex_env.ps1
├── setup_codex_env.bat
├── .codex-config.json
├── OFFLINE_ENV_README.md
├── activate_tests.log
└── ... (기타 프로젝트 파일)
```

- `offline_preparation/python_packages/` : 오프라인용 파이썬 패키지(.whl, .tar.gz)
- `offline_preparation/models/` : ML/임베딩 모델, NLTK 등 리소스, MODEL_MANIFEST.json
- `setup_codex_env.ps1` : PowerShell 오프라인 환경 자동 구축 스크립트
- `setup_codex_env.bat` : Batch(배치) 오프라인 환경 자동 구축 스크립트
- `.codex-config.json` : Codex 자동화 설정 파일
- `activate_tests.log` : pytest 자동 테스트 결과 로그

## 2. 오프라인 환경 설치 방법

### (1) PowerShell 사용 시

```powershell
PS C:\palantir> .\setup_codex_env.ps1
```

### (2) CMD/배치 환경 시

```bat
C:\palantir> setup_codex_env.bat
```

### (3) 설치 완료 메시지 예시

```
[✔] Offline env ready
```

## 3. Codex 실행 예시

```powershell
.\.venv\Scripts\Activate.ps1
codex --auto-edit
```

## 4. 설치 스크립트 실행 스크린샷 예시

(스크립트 실행 후 출력 예시를 캡처하여 첨부)

## 5. 흔한 오류 FAQ

- **Python 3.13이 설치되어 있지 않음**
  - `C:\Python313\python.exe` 경로에 64비트 Python 3.13이 반드시 설치되어 있어야 합니다.
- **패키지 설치 실패**
  - `install_errors.log` 또는 `build_offline_env.log`를 확인하세요.
  - requirements.txt에 명시된 패키지의 3.13 호환 wheel이 없으면, 버전을 낮춰 `req_fix.txt`에 기록 후 재시도하세요.
- **pytest 실패**
  - `activate_tests.log`에서 실패 테스트를 확인하고, Codex 추천 패치 주석을 추가하세요.

## 6. 모델/데이터 자산 관리

- `offline_preparation/models/` 내 모델 파일과 `MODEL_MANIFEST.json`의 체크섬을 반드시 확인하세요.

## 7. 기타 참고

- Codex는 `.venv`와 `.codex-config.json`만 인식하면 바로 개발을 이어받을 수 있습니다.
- 모든 로그는 `build_offline_env.log`에 저장됩니다.

---

문의/지원 필요 시 Sidebar Codex 또는 관리자에게 연락하세요.

## 1. 운영 환경 준비
- Python 3.10+ (venv 권장)
- 필수 패키지: requirements.txt 설치
- 환경변수: OPENAI_API_KEY 등 민감 정보는 .env 또는 환경변수로 관리
- MCP 계층(파일, 깃, 테스트 등)은 실제 운영 경로/권한/보안 정책에 맞게 설정

## 2. 테스트/품질/보안 체크리스트
- [x] pytest -v (단위/통합 테스트)
- [x] pytest --cov=palantir (커버리지 90% 이상 권장)
- [x] black --check . (코드 포매팅)
- [x] ruff . (린트/보안)
- [x] mypy . (정적 타입 분석)
- [x] .github/workflows/ci.yml (CI 자동화)
- [x] MCP 계층 경로/명령/쿼리 제한(보안)
- [x] 환경변수/API 키 하드코딩 금지
- [x] FastAPI/Streamlit 등 서버 CORS/인증/권한 설정
- [x] 로그/오류/감사 추적(운영 중 print→logging 모듈 권장)

## 3. 문서화 자동화
- README.md, AGENTS.md, OFFLINE_ENV_README.md 등 최신 구조/사용법/확장법 반영
- Mermaid 다이어그램(아키텍처/워크플로우/운영/보안 등) 활용
- 코드/테스트/운영/보안 변경 시 문서 동기화 필수

## 4. 운영 팁/베스트프랙티스
- MCP 계층은 실제 운영 환경(로컬/서버/클라우드)에 맞게 base_dir/repo_dir 등 경로 분리
- LLM API 호출은 토큰/비용/속도 제한 고려, 필요시 캐싱/재시도/로깅 추가
- 테스트/운영/자가개선 루프는 주기적(cron/APScheduler 등)으로 자동화 가능
- 운영 중 예외/오류는 반드시 로그로 남기고, 필요시 Slack/이메일 등 알림 연동
- 보안 취약점(경로/명령/입력/환경변수 등) 정기 점검

## 5. 참고/확장
- project.md, ai_agent_self_improvement.md, ai_agent.md 등 설계/로드맵/지침 참고
- 운영/보안/테스트 자동화 예시는 tests/, .github/workflows/, core/services/mcp/ 등 코드 참고 