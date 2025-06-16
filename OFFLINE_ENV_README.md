# Palantir 오프라인 환경 설정 및 운영 가이드

## 개요
이 문서는 Palantir를 오프라인 환경에서 설정하고 운영하는 방법을 상세히 설명합니다.

## 목차
1. [환경 준비](#환경-준비)
2. [의존성 설치](#의존성-설치)
3. [설정 파일](#설정-파일)
4. [보안 설정](#보안-설정)
5. [운영 가이드](#운영-가이드)
6. [문제 해결](#문제-해결)

## 환경 준비

### 시스템 요구사항
- Python 3.9+
- Docker 20.10+
- WSL2 (Windows 환경)
- 최소 8GB RAM
- 최소 50GB 저장공간

### 디렉토리 구조
```
palantir/
├── core/          # 핵심 기능
├── services/      # MCP 서비스
├── ontology/      # 데이터 모델
├── tests/         # 테스트 코드
├── config/        # 설정 파일
├── data/          # 데이터 저장소
└── logs/          # 로그 파일
```

## 의존성 설치

### 1. Poetry 설치
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. 의존성 설치
```bash
cd palantir
poetry install
```

### 3. 오프라인 패키지 준비
```bash
poetry export -f requirements.txt --output requirements.txt
pip download -r requirements.txt -d ./deps
```

## 설정 파일

### 1. 환경 변수
필수 환경 변수:
```bash
PALANTIR_ENV=offline
PALANTIR_LOG_LEVEL=INFO
PALANTIR_DATA_DIR=/path/to/data
PALANTIR_CONFIG_DIR=/path/to/config
```

### 2. 설정 파일 위치
- 기본 설정: `config/default.yaml`
- 오프라인 설정: `config/offline.yaml`
- 로깅 설정: `config/logging.yaml`
- 보안 설정: `config/security.yaml`

## 보안 설정

### 1. 접근 제어
- 파일 권한 설정
- 사용자 인증
- API 키 관리
- 네트워크 격리

### 2. 암호화
- 데이터 암호화
- 통신 암호화
- 키 관리
- 백업 암호화

### 3. 감사
- 접근 로그
- 변경 이력
- 보안 이벤트
- 주기적 검사

## 운영 가이드

### 1. 시작 및 종료
```bash
# 시작
./run_all.sh start

# 종료
./run_all.sh stop
```

### 2. 모니터링
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`
- 로그: `tail -f logs/palantir.log`

### 3. 백업
```bash
# 전체 백업
./scripts/backup.sh full

# 증분 백업
./scripts/backup.sh incremental
```

### 4. 성능 최적화
- 캐시 설정
- 메모리 관리
- 디스크 I/O
- 네트워크 최적화

## 문제 해결

### 1. 일반적인 문제
- 연결 오류
- 메모리 부족
- 디스크 공간 부족
- 성능 저하

### 2. 로그 분석
```bash
# 오류 로그 확인
grep ERROR logs/palantir.log

# 경고 로그 확인
grep WARN logs/palantir.log
```

### 3. 진단 도구
```bash
# 상태 확인
./scripts/health_check.sh

# 성능 프로파일링
./scripts/profile.sh
```

### 4. 문제 해결 절차
1. 증상 식별
2. 로그 분석
3. 진단 실행
4. 해결책 적용
5. 검증 및 모니터링

## 유지보수

### 1. 정기 점검
- 일일 점검
- 주간 점검
- 월간 점검
- 분기 점검

### 2. 업데이트
```bash
# 의존성 업데이트
poetry update

# 시스템 업데이트
./scripts/update.sh
```

### 3. 청소
```bash
# 로그 정리
./scripts/cleanup_logs.sh

# 임시 파일 정리
./scripts/cleanup_temp.sh
```

## 참고 자료
- [프로젝트 문서](./README.md)
- [에이전트 문서](./AGENTS.md)
- [기여 가이드](./CONTRIBUTING.md)
- [보안 정책](./SECURITY.md) 