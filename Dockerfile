# 1. uv 바이너리만 가져오기 위한 단계
FROM ghcr.io/astral-sh/uv:latest AS uv_bin

# 2. 실제 빌드 단계 (일반 python 이미지 사용)
FROM python:3.13-slim-bookworm AS builder

COPY --from=uv_bin /uv /uvx /bin/

WORKDIR /app

# 캐시 효율을 위해 의존성 파일만 먼저 복사
COPY uv.lock pyproject.toml ./

# 의존성 설치
RUN uv sync --frozen --no-install-project --no-dev

# 3. 최종 실행 단계
FROM python:3.13-slim-bookworm

WORKDIR /app

# builder에서 생성된 가상환경만 복사
COPY --from=builder /app/.venv /app/.venv

# 소스 코드 복사
COPY . .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8085

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8085"]
