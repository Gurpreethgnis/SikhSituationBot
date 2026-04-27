# Backend API — many hosts default to /opt/venv for Python; install gunicorn there.
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

# Native libs for psycopg2-binary, sentence-transformers / torch wheels, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /app

# Install server deps first (better layer cache)
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r /app/server/requirements.txt

COPY server /app/server

EXPOSE 8080

# PORT is set by Railway, Render, Fly, Cloud Run, etc. Use explicit venv path for hosts that invoke /opt/venv/bin/gunicorn.
ENTRYPOINT ["/bin/bash", "-c", "exec /opt/venv/bin/gunicorn --bind 0.0.0.0:${PORT:-8080} --workers ${WEB_CONCURRENCY:-2} --threads 4 --timeout 120 --access-logfile - --error-logfile - server.app:app"]
