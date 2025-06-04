# Codex 에이전트 가이드

## 개요

Codex 에이전트는 네트워크 차단 환경에서 동작하는 AI 기반 코드 분석 및 생성 도구입니다.

## 설치 및 설정

### 1. 시스템 요구사항

- Python 3.13
- 운영체제: Linux (x86_64) 또는 Windows
- 최소 8GB RAM
- 최소 20GB 저장공간

### 2. 오프라인 설치 준비

모든 필요한 패키지는 `offline_preparation/python_packages/unified` 디렉토리에 있습니다:

```bash
# Linux 환경
numpy-2.2.6-cp313-cp313t-manylinux_2_17_x86_64.manylinux2014_x86_64.whl

# Windows 환경
numpy-2.2.6-cp313-cp313-win_amd64.whl
```

### 3. 설치 과정

1. 의존성 설치:
```bash
python install_dependencies.py
```

이 스크립트는 다음 작업을 수행합니다:
- pip 업그레이드
- NumPy 설치 (시스템에 맞는 wheel 파일 사용)
- 기타 의존성 설치

2. 환경 변수 설정:
```bash
# Linux
export PYTHONPATH=/path/to/workspace
export OFFLINE_MODE=true

# Windows
set PYTHONPATH=C:\path\to\workspace
set OFFLINE_MODE=true
```

### 4. 설치 확인

```bash
pytest tests/ -v
```

## 기능

### 1. 코드 분석
- 정적 코드 분석
- 의미론적 코드 검색
- 파일 및 디렉토리 탐색
- 코드 문맥 이해

### 2. 코드 생성 및 수정
- 새로운 코드 생성
- 기존 코드 수정
- 버그 수정 및 리팩토링

### 3. 테스트 및 문서화
- 단위 테스트 생성
- API 문서 생성
- 코드 주석 추가

## 문제 해결 가이드

### 1. 설치 문제
- 시스템 아키텍처 확인
- Python 버전 호환성 검증
- wheel 파일 무결성 확인

### 2. 실행 시 문제
- 환경 변수 설정 확인
- 리소스 사용량 모니터링
- 로그 파일 분석

## 보안 설정

### 1. API 키 관리
- 환경 변수 사용
- 키 순환 정책 적용
- 접근 권한 제한

### 2. 코드 보안
- 소스 코드 격리
- 의존성 검사
- 취약점 스캔

## 모니터링 및 로깅

### 1. 성능 모니터링
- 리소스 사용량 추적
- 응답 시간 측정
- 에러율 모니터링

### 2. 로그 관리
- 상세 로그 기록
- 로그 순환 정책
- 문제 해결을 위한 로그 분석

## CI/CD 통합

### 1. 자동화된 테스트
```bash
pytest
pytest --cov
```

### 2. 코드 품질 관리
```bash
black .
ruff check .
mypy .
```

## 유지보수 및 업데이트

### 1. 정기적 업데이트
- 보안 패치 적용
- 의존성 버전 업그레이드
- wheel 파일 갱신

### 2. 문서화
- 변경 사항 기록
- API 문서 업데이트
- 사용자 가이드 유지보수

## 참고 사항

- 이 설정은 네트워크 차단 환경에 최적화되어 있습니다
- 모든 의존성은 로컬에서 해결됩니다
- Linux 환경에서는 manylinux wheel을 사용합니다
- Windows 환경에서는 win_amd64 wheel을 사용합니다

## 오류 해결

### 1. NumPy 설치 실패
- wheel 파일이 시스템 아키텍처와 일치하는지 확인
- pip 버전이 최신인지 확인
- setuptools와 wheel이 설치되어 있는지 확인

### 2. 의존성 충돌
- requirements.txt의 버전 호환성 확인
- 특정 패키지 버전 고정
- 가상 환경 사용 권장

### 3. 테스트 실패
- pytest 로그 확인
- 환경 변수 설정 검증
- 테스트 데이터 가용성 확인

## 개발 워크플로우

1. 환경 설정
```bash
python install_dependencies.py
```

2. 코드 품질 검사
```bash
black .
ruff check .
mypy .
```

3. 테스트 실행
```bash
pytest -v
```

4. 변경사항 커밋
```bash
git add .
git commit -m "feat: 기능 설명"
git push origin main
``` 