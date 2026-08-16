FROM python:3.12-slim

WORKDIR /app

COPY apps/worker/requirements.txt .
# Worker requires API dependencies as well because it imports API modules
COPY apps/api/requirements.txt api_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r api_requirements.txt

COPY apps/worker ./apps/worker
COPY apps/api ./apps/api
COPY modules ./modules
COPY packages ./packages
COPY scripts ./scripts

ENV PYTHONPATH=/app

RUN adduser --disabled-password --gecos '' celeryuser && chown -R celeryuser:celeryuser /app
USER celeryuser

CMD ["celery", "-A", "apps.worker.worker", "worker", "-l", "info", "--heartbeat-interval=30"]
