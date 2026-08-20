FROM node:22-bookworm-slim AS frontend
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html tsconfig*.json vite.config.* ./
COPY src ./src
COPY public ./public
RUN npm run build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy
WORKDIR /app
RUN pip install --no-cache-dir uv==0.11.29
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend ./backend
COPY scripts ./scripts
COPY --from=frontend /app/dist ./dist
RUN .venv/bin/python scripts/build_bootstrap_assets.py
EXPOSE 10000
CMD ["sh", "-c", ".venv/bin/uvicorn backend.asgi:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
