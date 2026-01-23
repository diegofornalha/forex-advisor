# Plano 06: Docker + Docker Compose

## Objetivo
Criar configuração Docker para rodar API + Redis com um comando.

## Arquivos
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

## Dockerfile

```dockerfile
FROM python:3.11-slim

# Metadados
LABEL maintainer="Diego"
LABEL description="Forex Advisor API - Remessa Online"

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho
WORKDIR /app

# Instala dependências de sistema (para sqlite-vec)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro (cache de layer)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY app/ ./app/
COPY rag_sdk/ ./rag_sdk/

# Expõe porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicialização
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: forex-advisor-api
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DEBUG=false
      - CACHE_TTL=3600
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: forex-advisor-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    command: redis-server --appendonly yes

volumes:
  redis_data:
    driver: local
```

## docker-compose.dev.yml (desenvolvimento)

```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: forex-advisor-api-dev
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DEBUG=true
    volumes:
      - ./app:/app/app  # Hot reload
    depends_on:
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## .dockerignore

```
# Git
.git
.gitignore

# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
.env
.venv
env/
venv/

# IDE
.idea
.vscode
*.swp
*.swo

# Testes
.pytest_cache
.coverage
htmlcov/
tests/

# Docs
*.md
!README.md
docs/

# Outros
.DS_Store
*.log
```

## Comandos

### Desenvolvimento
```bash
# Sobe com hot reload
docker-compose -f docker-compose.dev.yml up --build

# Logs
docker-compose logs -f api
```

### Produção
```bash
# Build e sobe
docker-compose up -d --build

# Verifica status
docker-compose ps

# Logs
docker-compose logs -f

# Para tudo
docker-compose down
```

### Úteis
```bash
# Rebuild sem cache
docker-compose build --no-cache

# Entra no container
docker-compose exec api bash

# Verifica Redis
docker-compose exec redis redis-cli ping

# Remove volumes (CUIDADO: perde dados)
docker-compose down -v
```

## requirements.txt (atualizado)

```
# API
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Cache
redis>=5.0.0

# Dados
yfinance>=0.2.18
pandas>=2.0.0
numpy>=1.24.0

# RAG
apsw>=3.44.0
sqlite-vec>=0.1.1
fastembed>=0.2.0

# LLM
anthropic>=0.18.0

# News
feedparser>=6.0.0
requests>=2.31.0

# Utils
python-dotenv>=1.0.0
```

## Variáveis de Ambiente

```bash
# .env (NÃO commitar!)
ANTHROPIC_API_KEY=sk-ant-api03-xxx
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600
DEBUG=false
```

```bash
# .env.example (commitar)
ANTHROPIC_API_KEY=your-key-here
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600
DEBUG=false
```

## Critérios de Sucesso
- [ ] `docker-compose up` sobe API + Redis
- [ ] Health check funcionando
- [ ] Hot reload em dev
- [ ] Volumes persistentes para Redis
- [ ] .dockerignore otimizado
- [ ] Imagem final < 500MB
