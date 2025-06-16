# Python 3.12 베이스 이미지 사용
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# 기본 도구 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN curl -sSL https://install.python-poetry.org | python3 -

# Poetry 설정
ENV PATH="/root/.local/bin:$PATH"
RUN poetry config virtualenvs.create false

# 의존성 파일 복사 및 설치
COPY pyproject.toml poetry.lock* ./
RUN poetry install --without dev --no-interaction --no-ansi

# 소스 코드 복사
COPY . .

# 포트 설정
EXPOSE 8000

# 실행 명령
CMD ["poetry", "run", "uvicorn", "palantir.main:app", "--host", "0.0.0.0", "--port", "8000"]
