# Palantir 오프라인 개발환경 구축 및 Codex 연동 가이드

## 1. 폴더 트리 및 구성 설명

```
C:\palantir\
├── offline_preparation\
│   ├── python_packages\
│   │   ├── main_app_packages\
│   │   └── pipeline_ui_packages\
│   ├── models\
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