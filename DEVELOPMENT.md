# Development Guide

This covers the basics for getting set up and working on the CloudGate project locally.

## Services

Here's what runs locally when you start everything up:

| Service | Port | Docs |
|---------|------|------|
| Gateway | 8000 | http://localhost:8000/docs |
| Auth | 8001 | http://localhost:8001/docs or /redoc |
| Profile | 8002 | http://localhost:8002/docs |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | http://localhost:3000 (admin/admin) |

## API Base URLs

When making API calls, use these base URLs:

- **Auth Service**: `http://localhost:8001`
  - `POST /api/v1/auth/register` - Register a new user
  - `POST /api/v1/auth/login` - Login and get tokens
  - `POST /api/v1/auth/refresh` - Refresh access token
  - `POST /api/v1/auth/logout` - Logout (requires auth)
  - `GET /api/v1/auth/me` - Get current user info (requires auth)
  - `POST /api/v1/auth/change-password` - Change password (requires auth)
  - `POST /api/v1/auth/verify-token` - Verify token validity (requires auth)
- **Gateway**: `http://localhost:8000`
  - Routes requests to appropriate services
- **Profile Service**: `http://localhost:8002`
  - Profile management endpoints

**Note**: Endpoints marked "(requires auth)" need an `Authorization: Bearer <token>` header with your access token from login.

## Making API Calls

Here are some examples of how to interact with the APIs:

```bash
# Register a new user
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "Test123!@#", "first_name": "John", "last_name": "Doe"}'

# Login to get tokens
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "Test123!@#"}'

# Get current user info (replace TOKEN with actual token)
curl -X GET http://localhost:8001/api/v1/auth/me \
  -H "Authorization: Bearer TOKEN"
```

You can also use the interactive docs at http://localhost:8001/docs to test endpoints directly in your browser.

## API Documentation

FastAPI automatically generates two types of documentation:

- **Swagger UI** (`/docs`): Interactive docs where you can actually test API endpoints right in your browser. Click "Try it out" on any endpoint to send real requests.
- **ReDoc** (`/redoc`): Clean, printable documentation that's great for sharing specs or reading through the API structure.

Both pull from the same source - your FastAPI route definitions and Pydantic models - so they're always in sync.

## Setup

Getting your local environment ready:

```bash
# Clone and setup
git clone https://github.com/amgad01/cloudgate.git && cd cloudgate
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

If you're new to this tech stack, here's a good order to learn things in:

1. **Python Async Basics**: Get comfortable with async/await and asyncio
2. **FastAPI**: Learn about routing, dependency injection, and middleware
3. **ASGI**: Understand how it differs from WSGI
4. **Uvicorn**: The ASGI server and how development reload works
5. **Pydantic v2**: Data validation and configuration management
6. **SQLAlchemy 2.0**: Async ORM patterns and working with asyncpg
7. **Alembic**: Handling database schema changes
8. **Redis**: Using the async client for caching
9. **JWT & Security**: Token handling and password security
10. **Docker**: Building images, running containers, and using compose
11. **Prometheus & Grafana**: Setting up metrics and dashboards
12. **TypeScript**: Frontend components (if you work on the UI)

## Project Organization

**Key folders to know**:
- `services/` — The microservices (gateway, auth, profile). Each has a `main.py` for the FastAPI app and `api/routes.py` for the endpoints
- `shared/` — Common code like `config.py`, database connections, middleware, and data schemas
- `docker/` — Dockerfiles for building the service images
- `docker-compose.yml` — How everything runs together locally
- `infrastructure/` — AWS setup code using CDKTF
- `tests/` — Unit and integration tests
- `pyproject.toml` — Python dependencies and project config
- `Makefile` — Handy shortcuts for common tasks

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/amgad01/cloudgate.git
cd cloudgate
```

## Running the Services

```bash
# Start everything
make dev
# or
docker-compose up -d

# Check that containers are running
docker-compose ps

# Follow logs for a specific service
docker-compose logs -f gateway
```

## Testing

```bash
# Run all tests
make test

# Run a specific test file
pytest tests/unit/test_auth.py -v

# Run just one test with shorter output
pytest -k "test_login" --tb=short
```

## Reset Database

```bash
bash scripts/reset-db.sh
```

## Common Commands

```bash
make dev                # Start all services
make test               # Run the test suite
make docker-build       # Build container images
docker-compose logs -f  # Follow logs from all services
```

## Debugging

```bash
# Connect to the database
docker-compose exec postgres psql -U postgres -d cloudgate

# Get a shell in a running container
docker-compose exec gateway bash

# Check recent logs for a service
docker-compose logs -f gateway --tail=50
```

## Configuration

The default settings for development are in `docker-compose.yml`. If you need to override anything locally, create a `.env` file:

```bash
# .env (don't commit this file)
DEBUG=true
DATABASE_URL=postgresql://...
```

## Code Style

We follow these conventions:
- **Python**: PEP 8 with Black formatting and 4-space indentation
- **TypeScript**: Strict mode, no `any` types allowed
- Pre-commit hooks will enforce these rules when you commit

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
# Check for port conflicts
lsof -i :8000

# Completely rebuild everything
docker-compose down -v && docker-compose up -d --build

# Reset the database if things are messed up
bash scripts/reset-db.sh

# Get detailed output from failing tests
pytest tests/unit/test_auth.py -vv --tb=long
```

## Getting Started

1. Run `make dev` to start everything
2. Open http://localhost:8000/docs to see the gateway API
3. Look at `services/gateway/main.py` to understand the app structure
4. Check out `tests/unit/` to see how we write tests
