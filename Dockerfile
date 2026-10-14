# Build the frontend.
FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# Run the backend, which also serves the built frontend.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev
COPY core ./core
COPY server ./server
COPY --from=web /web/dist ./web/dist
ENV MTM_DATABASE_URL=sqlite:////data/app.db
EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "server.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
