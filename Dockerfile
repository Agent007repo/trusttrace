FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev
CMD ["uv", "run", "--no-sync", "uvicorn", "trusttrace.app:app", "--host", "0.0.0.0", "--port", "8000"]
