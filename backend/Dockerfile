# Multi-stage: build the Vue SPA with Node, then serve it + the API from Python.

# --- 1. build the frontend ------------------------------------------------
FROM node:20-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json* ./
RUN npm install
COPY web/ ./
RUN npm run build

# --- 2. python runtime ----------------------------------------------------
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
# Built SPA lands where main.py's CCTRACKER_STATIC_DIR points.
COPY --from=web /web/dist ./static

ENV CCTRACKER_STATIC_DIR=/app/static
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
