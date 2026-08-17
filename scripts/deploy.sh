#!/bin/bash
set -e

echo "========================================================="
echo "   KS FoodOps ERP - Automated Cloud Deployment Script    "
echo "========================================================="

# 1. Update and install prerequisites if needed
if ! command -v docker &> /dev/null; then
    echo "[1/5] Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

if ! docker compose version &> /dev/null; then
    echo "[2/5] Installing Docker Compose Plugin..."
    apt-get update && apt-get install -y docker-compose-plugin
fi

# 2. Check if .env exists
if [ ! -f .env ]; then
    echo "[3/5] Creating .env from .env.example..."
    cp .env.example .env
    # Generate random secrets
    JWT_RANDOM=$(openssl rand -hex 32)
    sed -i "s/replace_with_a_secure_minimum_32_bytes_random_secret_string_here_123456/$JWT_RANDOM/g" .env
fi

# 3. Pull & Build Containers
echo "[4/5] Building and launching containers..."
docker compose up -d --build

# 4. Run database migrations
echo "[5/5] Running database migrations with RLS..."
docker compose exec -T api alembic upgrade head

echo "========================================================="
echo "   🎉 KS FoodOps is UP and RUNNING!                      "
echo "   Web Panel: http://localhost:3000                      "
echo "   API Docs:  http://localhost:8000/docs                 "
echo "========================================================="
