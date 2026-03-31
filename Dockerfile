# Stage 1: Build Next.js static export
FROM node:22-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app/backend

# Install Python dependencies
COPY backend/pyproject.toml .
RUN uv pip install --system --no-cache fastapi "uvicorn[standard]" aiosqlite

COPY backend/ .

# Copy built frontend into the static directory FastAPI will serve
COPY --from=frontend-builder /app/frontend/out ./static

RUN mkdir -p /data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
