# ===== Stage 1: Builder =====
FROM python:3.11-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency files — leverage Docker layer cache
COPY pyproject.toml uv.lock ./

# Install dependencies vào /app/.venv, không install project package
RUN uv sync --frozen --no-install-project --no-dev

# ===== Stage 2: Runtime =====
FROM python:3.11-slim

WORKDIR /app

# Copy virtualenv từ builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Đặt PATH để dùng venv
ENV PATH="/app/.venv/bin:$PATH"

# Expose FastAPI port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
