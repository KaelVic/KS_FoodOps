#!/bin/bash
set -e

echo "========================================================="
echo "   🚀 KS FoodOps — Script de Instalação Automática      "
echo "========================================================="

# 1. Atualizar pacotes do sistema
echo "📦 [1/6] Atualizando pacotes do sistema..."
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y curl git ufw debian-keyring debian-archive-keyring apt-transport-https

# 2. Instalar Docker e Docker Compose
echo "🐳 [2/6] Instalando Docker Engine..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker $USER
fi

# 3. Instalar Caddy (HTTPS Automático)
echo "🔒 [3/6] Instalando Caddy Web Server..."
if ! command -v caddy &> /dev/null; then
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
    sudo apt-get update -y
    sudo apt-get install caddy -y
fi

# 4. Configurar Firewall UFW
echo "🛡️  [4/6] Configurando Firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# 5. Gerar chaves e arquivo .env se não existir
echo "⚙️  [5/6] Verificando arquivo de ambiente (.env)..."
if [ ! -f .env ]; then
    JWT_SECRET=$(openssl rand -hex 32)
    REDIS_PASSWORD=$(openssl rand -hex 16)
    
    cat <<EOF > .env
ENVIRONMENT=production
JWT_SECRET=${JWT_SECRET}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Configure a URL do Supabase abaixo:
DATABASE_URL=postgresql+asyncpg://postgres:sua_senha@seu_supabase_host:5432/postgres
OWNER_DATABASE_URL=postgresql+asyncpg://postgres:sua_senha@seu_supabase_host:5432/postgres

REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

NEXT_PUBLIC_API_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
STORAGE_BUCKET_NAME=ks-foodops-protected-docs
EOF
    echo "⚠️ Arquivo .env criado com chaves geradas! Configure o DATABASE_URL com o seu Supabase antes de continuar."
fi

echo "========================================================="
echo "✅ Servidor preparado com sucesso!"
echo "Para subir a aplicação e aplicar migrações:"
echo "1. Edite o .env com sua URL do Supabase: nano .env"
echo "2. Execute: docker compose -f docker-compose.prod.yml up -d --build"
echo "3. Aplique as migrações: docker compose -f docker-compose.prod.yml exec api alembic upgrade head"
echo "========================================================="
