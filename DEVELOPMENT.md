# Development Guide

Quick setup and common commands for local development.

## Services

| Service | Port | Docs |
|---------|------|------|
| Gateway | 8000 | http://localhost:8000/docs |
| Auth | 8001 | http://localhost:8001/docs |
| Profile | 8002 | http://localhost:8002/docs |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | http://localhost:3000 |

## Setup

```bash
# Clone and setup
git clone <repo> && cd cloudgate
python3.13 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e ".[dev]"
pre-commit install
```

#### Windows (WSL2)
```bash
# Install Docker Desktop for Windows with WSL2 integration

# In WSL2 Ubuntu shell:
sudo apt update && sudo apt install -y \
  python3.13 python3.13-venv python3.13-dev \
  nodejs git build-essential
```

## Developer Onboarding

If you're new to this stack, ramp up efficiently in this order:

1. **Python Async Basics**: async/await, asyncio
2. **FastAPI**: Routing, dependency injection, middleware
3. **ASGI**: Understanding ASGI vs WSGI
4. **Uvicorn**: ASGI server and development reload
5. **Pydantic v2**: Data validation and settings
6. **SQLAlchemy 2.0**: Async ORM patterns and asyncpg
7. **Alembic**: Database migrations
8. **Redis**: Async client usage
9. **JWT & Security**: Token management, password hashing
10. **Docker**: Images, containers, compose
11. **Prometheus & Grafana**: Metrics and dashboards
12. **TypeScript**: Frontend components (if working on UI)

## Project Organization

**Key Folders**:
- `services/` — Microservices (gateway, auth, profile)
  - Each service has `main.py` (FastAPI app setup) and `api/routes.py`
- `shared/` — Shared code (`config.py`, `database/`, `middleware/`, `schemas/`)
- `docker/` — Dockerfiles for services
- `docker-compose.yml` — Local development orchestration
- `infrastructure/` — AWS infrastructure code (CDKTF)
- `tests/` — Unit and integration tests
- `pyproject.toml` — Python dependencies and packaging config
- `Makefile` — Common commands

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/cloudgate-api-gateway.git
cd cloudgate-api-gateway
```

## Running

```bash
# Start all services
make dev
# or
docker-compose up -d

# Verify containers
docker-compose ps

# View logs
docker-compose logs -f gateway
```

## Testing

```bash
# Run all tests
make test

# Specific test
pytest tests/unit/test_auth.py -v

# Watch mode
pytest -k "test_login" --tb=short
```

## Reset Database

```bash
bash scripts/reset-db.sh
```

## Common Commands

```bash
make dev                # Start all services
make test               # Run tests
make docker-build       # Build images
docker-compose logs -f  # View logs
```

## Debugging

```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d cloudgate

# Enter service container
docker-compose exec gateway bash

# Check service logs
docker-compose logs -f gateway --tail=50
```

## Configuration

Development defaults are in `docker-compose.yml`. For local overrides, create `.env`:

```bash
# .env (not committed)
DEBUG=true
DATABASE_URL=postgresql://...
```

## Code Style

- Python: PEP 8, Black formatter, 4-space indent
- TypeScript: Strict mode, no `any` types
- Pre-commit hooks enforce style on commit

## Architecture Patterns

**Async database:**
```python
async def get_user(user_id: int):
    async with get_db_session() as session:
        return await session.get(User, user_id)
```

**Dependency injection:**
```python
async def get_current_user(token: str = Depends(get_token)):
    return verify_token(token)
```

**Error handling:**
```python
raise HTTPException(status_code=400, detail="Invalid request")
```

## Troubleshooting

```bash
# Port conflicts
lsof -i :8000

# Rebuild from scratch
docker-compose down -v && docker-compose up -d --build

# Database errors
bash scripts/reset-db.sh

# Test failures
pytest tests/unit/test_auth.py -vv --tb=long
```

## Next

1. Run `make dev`
2. Open http://localhost:8000/docs
3. Check `services/gateway/main.py` for app structure
4. Review `tests/unit/` for testing patterns

