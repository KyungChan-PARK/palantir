FROM python:3.12-slim AS builder
WORKDIR /install
COPY requirements/base.txt ./requirements.txt
RUN pip install --upgrade pip \
    && pip wheel --wheel-dir /install -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY --from=builder /install /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels
COPY . /app
EXPOSE 8000
CMD ["python", "main.py"]
