FROM python:3.12-slim

WORKDIR /app

COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api ./apps/api
COPY apps/worker ./apps/worker
COPY modules ./modules
COPY packages ./packages
COPY scripts ./scripts
COPY alembic ./alembic
COPY alembic.ini .

ENV PYTHONPATH=/app

RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app

# Ensure we have postgresql-client for pg_isready and dos2unix for crlf issues
RUN apt-get update && apt-get install -y postgresql-client dos2unix && rm -rf /var/lib/apt/lists/*

COPY apps/api/entrypoint.sh /app/entrypoint.sh
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

USER appuser

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
