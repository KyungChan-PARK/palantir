# Python 3.12 베이스 이미지 사용
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN curl -sSL https://install.python-poetry.org | python3 -

# 프로젝트 파일 복사
COPY pyproject.toml poetry.lock ./
COPY src/ ./src/
COPY tests/ ./tests/
COPY scripts/ ./scripts/

# 의존성 설치
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 포트 설정
EXPOSE 8000 8501

# 실행 스크립트 복사
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 진입점 설정
ENTRYPOINT ["docker-entrypoint.sh"] 