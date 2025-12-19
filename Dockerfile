FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ARG DATABASE_URL
ARG MODEL_URL


ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

COPY src/ ./src/
RUN mkdir -p /app/data/raw /app/output

CMD ["uv", "run", "python", "src/models/inference.py", "data/raw/teste.pdf"]