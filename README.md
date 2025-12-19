# CloudGate API Gateway

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Minimal, production-style API gateway and microservices in Python. FastAPI + PostgreSQL + Redis with Docker Compose for local dev and CDKTF for AWS.

## Quick Start

```bash
git clone https://github.com/yourusername/cloudgate.git
cd cloudgate

make install
docker-compose up -d

# Services
# - Gateway: http://localhost:8000
# - Auth: http://localhost:8001/docs
# - Grafana: http://localhost:3000 (admin/admin)
```

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
