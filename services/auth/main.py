from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from prometheus_client import make_asgi_app

from services.auth.api.routes import router
from shared.config import get_auth_config
from shared.database.connection import init_database
from shared.database.redis import init_redis
from shared.middleware.logging import LoggingMiddleware, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    config = get_auth_config()

    if config.app_env == "production":
        if (
            "change-me" in config.secret_key.lower()
            or "change-me" in config.jwt_secret_key.lower()
        ):
            raise ValueError(
                "Default secrets detected in production environment. "
                "Please set SECRET_KEY and JWT_SECRET_KEY environment variables."
            )

    setup_logging(config)
    db = init_database(config)
    redis = init_redis(config)

    yield

    await db.close()
    await redis.close()


def create_app() -> FastAPI:
    config = get_auth_config()

    tags_metadata = [
        {
            "name": "Authentication",
            "description": (
                "User authentication and JWT token management endpoints. "
                "Use these endpoints to register users, login, manage tokens, and change passwords."
            ),
        },
    ]

    app = FastAPI(
        title="CloudGate Auth Service",
        description=(
            "🔐 **Authentication and Authorization Service** for CloudGate API Gateway\n\n"
            "This service handles all user authentication, JWT token management, and user profile operations. "
            "All protected endpoints require a valid JWT Bearer token in the Authorization header.\n\n"
            "## Key Features:\n"
            "- User registration with email and secure password requirements\n"
            "- JWT-based authentication with access and refresh tokens\n"
            "- Token refresh mechanism (30-minute access token expiration)\n"
            "- Password hashing with Argon2 algorithm\n"
            "- User profile management (view, change password)\n"
            "- Token verification and logout functionality\n"
            "- Health check endpoint for service monitoring\n\n"
            "## Getting Started:\n"
            "1. **Register**: `POST /api/v1/auth/register` - Create a new user account\n"
            "2. **Login**: `POST /api/v1/auth/login` - Get access and refresh tokens\n"
            "3. **Access Protected Resources**: Add `Authorization: Bearer {access_token}` header to requests\n"
            "4. **Refresh Token**: `POST /api/v1/auth/refresh` - Get new tokens when expired\n"
            "5. **Logout**: `POST /api/v1/auth/logout` - Invalidate tokens\n\n"
            "## Password Requirements:\n"
            "- Length: 8-128 characters\n"
            '- Must contain: uppercase letter (A-Z), lowercase letter (a-z), digit (0-9), special character (!@#$%^&*(),.?":{}|<>)\n\n'
            "## API Documentation:\n"
            "- **Swagger UI**: `/docs` (interactive, try-it-out enabled)\n"
            "- **ReDoc**: `/redoc` (beautiful, read-only documentation)\n"
            "- **OpenAPI Schema**: `/openapi.json` (machine-readable)\n"
            "- **Metrics**: `/metrics` (Prometheus metrics for monitoring)\n"
            "- **Health Check**: `/api/v1/health` (service health status)\n\n"
            "## Authentication Methods:\n"
            "**Bearer Token (JWT):**\n"
            "```\n"
            "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...\n"
            "```\n\n"
            "## Common Response Codes:\n"
            "- **200 OK**: Successful operation\n"
            "- **201 Created**: User successfully registered\n"
            "- **400 Bad Request**: Invalid input or validation failed\n"
            "- **401 Unauthorized**: Missing or invalid authentication token\n"
            "- **409 Conflict**: Email already registered\n"
            "- **500 Internal Server Error**: Server error\n\n"
            "## Support & Documentation:\n"
            "For detailed endpoint documentation, see the 'Authentication' section below or visit the Swagger UI at `/docs`"
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        openapi_tags=tags_metadata,
        contact={
            "name": "CloudGate Team",
            "url": "https://github.com/cloudgate",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(LoggingMiddleware, service_name="auth")

    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    app.include_router(router, prefix="/api/v1")

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def root() -> str:
        return """
        <html>
            <head><title>CloudGate Auth Service</title></head>
            <body>
                <h1>CloudGate Auth Service</h1>
                <p>API Documentation: <a href="/docs">/docs</a></p>
                <p>ReDoc: <a href="/redoc">/redoc</a></p>
            </body>
        </html>
        """

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    config = get_auth_config()
    uvicorn.run(
        "services.auth.main:app",
        host="0.0.0.0",
        port=config.service_port,
        reload=config.debug,
    )
