#!/bin/sh
set -e

# Wait for database to be ready
echo "Waiting for database..."
while ! pg_isready -d $OWNER_DATABASE_URL; do
  sleep 1
done
echo "Database is ready."

# Run migrations using the ks_owner role (via OWNER_DATABASE_URL)
echo "Running database migrations..."
# We explicitly set the DATABASE_URL to OWNER_DATABASE_URL so alembic uses it.
export DATABASE_URL=$OWNER_DATABASE_URL
alembic upgrade head

echo "Migrations completed."

# Reset DATABASE_URL back to APP_DATABASE_URL (which should be injected from environment)
# Actually we can just let uvicorn run with the original env vars, 
# since we used export DATABASE_URL=$OWNER_DATABASE_URL it affects the current shell, 
# but we can reset it to not pass it to the app if we want.
# Actually it's better to run alembic explicitly:
# PYTHONPATH=/app alembic -x db_url=$OWNER_DATABASE_URL upgrade head (if alembic.ini supports it)
# Since Alembic uses os.environ.get("DATABASE_URL"), the export above works for alembic.

# Re-export the original DATABASE_URL for the app
export DATABASE_URL=$APP_DATABASE_URL

echo "Starting Uvicorn..."
exec uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
