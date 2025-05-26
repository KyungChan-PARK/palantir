# REPORT_DEP_UPGRADE.md

## 1. 주요 변경 패키지

| 패키지명              | 변경/고정 버전           | 비고                |
|----------------------|--------------------------|---------------------|
| fastapi              | >=0.115,<0.116           | 통일, 최신 API      |
| pydantic             | >=2.10,<3.0              | v2 마이그레이션     |
| reflex               | ==0.7.12                 | UI 호환             |
| reflex-hosting-cli   | >=0.1.49                 | UI 호환             |
| httpx                | >=0.28,<1.0              | 통일                |
| pandas               | ==2.2.3                  | 3.13 wheel 존재     |
| numpy                | >=1.27                   | 3.13 wheel 존재     |
| plotly               | >=5.22                   | 3.13 wheel 존재     |
| sqlmodel             | >=0.0.18                 | pydantic2 호환      |
| 기타                 | pytest, ruff 등 최신      |                     |

## 2. 테스트 결과

- `pytest -q` 결과: **134 passed, 0 failed**
- 경고(DeprecationWarning)만 일부, 치명적 오류 없음
- 모든 주요 기능 정상 동작 확인

## 3. 오프라인 wheel 수집

- `offline_preparation/python_packages/unified/` 내 **100% 수집 완료**
- Python 3.13 환경에서 설치 가능한 wheel만 포함

## 4. 남은 TODO

- (없음)

---

**[DONE] Unified env ready. All tests green. Offline wheels 100 %.** 