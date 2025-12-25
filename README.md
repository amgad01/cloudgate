# CloudGate API Gateway

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A minimal, production-ready API gateway and microservices setup built with Python. Uses FastAPI, PostgreSQL, and Redis, with Docker Compose for local development and CDKTF for AWS deployment.

## Quick Start

Getting up and running is straightforward:

```bash
git clone https://github.com/amgad01/cloudgate.git
cd cloudgate

make install
docker-compose up -d
```

Once everything's running, you'll have these services available:
- **Gateway**: http://localhost:8000
- **Auth Service**: http://localhost:8001/docs (Swagger UI) or /redoc (ReDoc)
- **Grafana**: http://localhost:3000 (login with admin/admin)

## Architecture

```
ALB → API Gateway (rate limit, circuit breaker, logging)
   ├→ Auth Service (JWT, user management)
   ├→ Profile Service (user profiles)
   └→ PostgreSQL + Redis
```

## Tech Stack

- **Python 3.13+** with FastAPI and async SQLAlchemy
- **PostgreSQL 15** and **Redis 7**
- **TypeScript** frontend (no framework)
- **Docker Compose** for local dev
- **CDKTF** for AWS deployment
- **Prometheus + Grafana** monitoring

## API Documentation

FastAPI gives you two ways to explore the API docs:

- **Swagger UI** (`/docs`): The interactive version where you can actually test endpoints directly in your browser. Super handy for development.
- **ReDoc** (`/redoc`): A clean, printable layout that's better for sharing API specs or just reading through everything.

Both are generated automatically from your FastAPI routes and Pydantic models, so they're always up to date.

Note: The Auth login endpoint enforces strict payload validation — unknown/extra request fields are rejected with HTTP 422.

## Structure

```
cloudgate/
├── services/          # Microservices (gateway, auth, profile)
├── shared/            # Database, middleware, schemas
├── tests/             # Unit and integration tests
├── docker/            # Dockerfiles
├── infrastructure/    # CDKTF AWS deployment
├── scripts/           # Utilities (reset-db, reset-grafana)
└── Makefile          # Build commands
```

## Features

- Request routing and static file serving
- JWT authentication with refresh tokens
- Rate limiting and circuit breaker
- Async database and cache operations
- Prometheus metrics and Grafana dashboards
- CSRF and input validation
- Comprehensive test coverage

## Development

```bash
# Start all services
make dev

# Run tests
make test

# View logs
docker-compose logs -f gateway
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup and commands.

## Reset Utilities

**Grafana:**
```bash
bash scripts/reset-grafana.sh  # Reset admin password or factory reset
```

**Database:**
```bash
bash scripts/reset-db.sh  # Drop and recreate database schema
```

## Security

- JWT tokens with refresh capability
- Argon2 password hashing
- CSRF protection
- Rate limiting
- Circuit breaker for downstream services
- Input sanitization

## Deployment

Deploy to AWS with CDKTF:

```bash
cd infrastructure/cdktf
npm install
cdktf deploy
```

## License

MIT
