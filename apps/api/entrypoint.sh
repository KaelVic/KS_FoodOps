#!/bin/sh
set -e

echo "Waiting for database connection..."
python -c "
import sys, time, os, asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

db_url = os.environ.get('OWNER_DATABASE_URL') or os.environ.get('DATABASE_URL')
if not db_url:
    print('No database url configured, skipping wait.')
    sys.exit(0)

if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql+asyncpg://', 1)
elif db_url.startswith('postgresql://'):
    db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

async def check():
    for i in range(15):
        try:
            engine = create_async_engine(db_url)
            async with engine.connect() as conn:
                await conn.execute(text('SELECT 1'))
            await engine.dispose()
            print('Database is ready!')
            return
        except Exception as e:
            print(f'Waiting for db ({i+1}/15)...')
            time.sleep(2)
    print('Database wait finished, proceeding...')

asyncio.run(check())
"

echo "Running database migrations..."
alembic upgrade head || echo "Migration notice: continuing..."

echo "Starting Uvicorn..."
exec uvicorn apps.api.main:app --host 0.0.0.0 --port 8000

