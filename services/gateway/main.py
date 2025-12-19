from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app

from services.gateway.api.routes import router
from services.gateway.services.proxy_service import ProxyService
from shared.config import get_gateway_config
from shared.database.redis import init_redis
from shared.middleware.circuit_breaker import CircuitBreaker, CircuitBreakerMiddleware
from shared.middleware.logging import LoggingMiddleware, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    config = get_gateway_config()

    # Validate secrets in production
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

    redis = init_redis(config)

    app.state.proxy_service = ProxyService(config=config)

    yield

    # Cleanup
    await app.state.proxy_service.close()
    await redis.close()


def create_app() -> FastAPI:
    config = get_gateway_config()

    # OpenAPI tags metadata for better documentation organization
    tags_metadata = [
        {
            "name": "Gateway",
            "description": (
                "API Gateway endpoints for routing, health checks, and metrics. "
                "The gateway is the main entry point for all API requests and handles request routing, rate limiting, and circuit breaking."
            ),
        },
    ]

    app = FastAPI(
        title="CloudGate API Gateway",
        description=(
            "🚀 **Central API Gateway** for CloudGate Microservices\n\n"
            "This is the main entry point for all API requests. It provides intelligent request routing, "
            "rate limiting, circuit breaker protection, and comprehensive monitoring through Prometheus metrics.\n\n"
            "## Key Features:\n"
            "- **Request Routing**: Intelligently routes requests to backend services (Auth, etc.)\n"
            "- **Rate Limiting**: Token bucket algorithm with Redis-backed rate limiting (protects backend)\n"
            "- **Circuit Breaker**: Automatic fault tolerance - stops requests to unhealthy services\n"
            "- **Request Logging**: Structured logging with request/response tracking\n"
            "- **CORS Support**: Cross-origin request handling for web clients\n"
            "- **Prometheus Metrics**: Comprehensive metrics for monitoring and alerting\n"
            "- **Health Checks**: Real-time service health monitoring\n\n"
            "## Architecture:\n"
            "```\n"
            "┌─────────────────────────────────────────────┐\n"
            "│  Client (Browser, API Client, Mobile App)   │\n"
            "└────────────────┬────────────────────────────┘\n"
            "                 │\n"
            "    ┌────────────▼─────────────────┐\n"
            "    │   CloudGate API Gateway      │\n"
            "    │  (localhost:8000)            │\n"
            "    │  ├─ Rate Limiter             │\n"
            "    │  ├─ Circuit Breaker          │\n"
            "    │  ├─ Request Router           │\n"
            "    │  └─ Logging Middleware       │\n"
            "    └────────────┬──────────────────┘\n"
            "                 │\n"
            "    ┌────────────┴──────────────────┐\n"
            "    │                               │\n"
            "┌───▼────────────────┐  ┌──────────▼────────┐\n"
            "│  Auth Service      │  │  Other Services   │\n"
            "│  (localhost:8001)  │  │  (Future)         │\n"
            "└────────────────────┘  └───────────────────┘\n"
            "```\n\n"
            "## Quick Navigation:\n"
            "- **API Documentation**: `/docs` (Swagger UI - interactive)\n"
            "- **Alternative Docs**: `/redoc` (ReDoc - beautiful, read-only)\n"
            "- **OpenAPI Schema**: `/openapi.json` (machine-readable)\n"
            "- **Health Check**: `/api/v1/health` (service status)\n"
            "- **Prometheus Metrics**: `/metrics` (for monitoring)\n\n"
            "## Rate Limiting:\n"
            "- **Algorithm**: Token bucket with Redis\n"
            "- **Default Limit**: Configurable per endpoint\n"
            "- **Response on Limit**: HTTP 429 Too Many Requests\n"
            "- **Headers**: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset\n\n"
            "## Circuit Breaker States:\n"
            "- **CLOSED** (Normal): Requests flow normally to backend services\n"
            "- **OPEN** (Failure Detected): Requests immediately rejected with 503 Service Unavailable\n"
            "- **HALF_OPEN** (Recovery Mode): Limited requests allowed to test backend recovery\n\n"
            "## Monitoring & Observability:\n"
            "- **Prometheus**: `/metrics` endpoint exposes all metrics\n"
            "- **Grafana**: http://localhost:3000 for dashboards and alerts\n"
            "- **Structured Logs**: JSON-formatted logs for easy parsing\n\n"
            "## Error Responses:\n"
            "- **400 Bad Request**: Invalid request format\n"
            "- **429 Too Many Requests**: Rate limit exceeded\n"
            "- **500 Internal Server Error**: Gateway error\n"
            "- **502 Bad Gateway**: Backend service error\n"
            "- **503 Service Unavailable**: Circuit breaker OPEN (backend unhealthy)\n"
            "- **504 Gateway Timeout**: Request timeout\n\n"
            "## Support:\n"
            "See the 'Gateway' section below for endpoint details, or visit `/docs` for interactive documentation."
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

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Middleware Stack (Applied in Reverse Order) ───────────────────────────
    # Why this ordering:
    #   1. LoggingMiddleware wraps all requests → captures full lifecycle metrics.
    #   2. CircuitBreakerMiddleware fails fast when backends are unhealthy → prevents
    #      wasted proxy attempts and reduces cascading failures.
    #   3. (RateLimiterMiddleware if added later would go here, before circuit breaker.)
    # Operational note:
    #   Exclude health/docs/metrics from circuit breaker so monitoring and status
    #   checks remain responsive even when backends are down.

    # Add logging middleware
    app.add_middleware(LoggingMiddleware, service_name="gateway")

    # Add circuit breaker middleware
    circuit_breaker = CircuitBreaker(
        name="gateway",
        failure_threshold=config.circuit_breaker_failure_threshold,
        recovery_timeout=config.circuit_breaker_recovery_timeout,
    )
    app.add_middleware(
        CircuitBreakerMiddleware,
        circuit_breaker=circuit_breaker,
        exclude_paths=["/health", "/metrics", "/docs", "/redoc", "/openapi.json"],
    )

    # Mount Prometheus metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # Mount static files for UI
    import os

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="static")

    # Include routers
    app.include_router(router, prefix="/api/v1")

    # Add root redirect to homepage
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def root() -> str:
        import pathlib

        index_path = pathlib.Path(__file__).parent / "static" / "index.html"
        if index_path.exists():
            return index_path.read_text()

        # Fallback if static files don't exist
        return """
<!DOCTYPE html>
<html>
<head>
    <title>CloudGate API Gateway</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .content {
            padding: 40px;
        }
        .section {
            margin-bottom: 30px;
        }
        .section h2 {
            color: #667eea;
            font-size: 1.5em;
            margin-bottom: 15px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .section ul, .section ol {
            margin-left: 20px;
        }
        .section li {
            margin-bottom: 8px;
        }
        .buttons {
            display: flex;
            gap: 12px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
            font-size: 1em;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
            border: 2px solid #667eea;
        }
        .btn-secondary:hover {
            background: #667eea;
            color: white;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .feature-card {
            background: #f9f9f9;
            border-left: 4px solid #667eea;
            padding: 15px;
            border-radius: 6px;
        }
        .feature-card h3 {
            color: #667eea;
            margin-bottom: 8px;
            font-size: 1em;
        }
        .feature-card p {
            color: #555;
            font-size: 0.95em;
        }
        code {
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            color: #d63384;
        }
        .status {
            display: inline-block;
            padding: 4px 8px;
            background: #28a745;
            color: white;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
            margin-top: 10px;
        }
        .architecture {
            background: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 15px;
            font-family: monospace;
            font-size: 0.85em;
            overflow-x: auto;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 CloudGate API Gateway</h1>
            <p>Central Entry Point for Microservices</p>
            <div class="status">ACTIVE</div>
        </div>
        <div class="content">
            <div class="section">
                <h2>Overview</h2>
                <p>Welcome to the CloudGate API Gateway! This is the central entry point for all API requests
                in the CloudGate microservices ecosystem. The gateway provides intelligent request routing,
                   rate limiting, circuit breaker protection, and comprehensive monitoring.</p>
                <p style="margin-top: 10px;"><strong>Version:</strong> 1.0.0 | <strong>Status:</strong> Healthy ✓</p>
            </div>

            <div class="section">
                <h2>📚 Documentation</h2>
                <p>Choose your preferred documentation format:</p>
                <div class="buttons">
                    <a href="/docs" class="btn btn-primary">🎯 Swagger UI (Interactive)</a>
                    <a href="/redoc" class="btn btn-secondary">📖 ReDoc (Beautiful)</a>
                    <a href="/openapi.json" class="btn btn-secondary">⚙️ OpenAPI Schema</a>
                </div>
            </div>

            <div class="section">
                <h2>⚡ Key Features</h2>
                <div class="feature-grid">
                    <div class="feature-card">
                        <h3>🔀 Request Routing</h3>
                        <p>Intelligent request routing to backend services</p>
                    </div>
                    <div class="feature-card">
                        <h3>⏱️ Rate Limiting</h3>
                        <p>Token bucket algorithm for traffic control</p>
                    </div>
                    <div class="feature-card">
                        <h3>🔌 Circuit Breaker</h3>
                        <p>Automatic fault tolerance protection</p>
                    </div>
                    <div class="feature-card">
                        <h3>📝 Logging</h3>
                        <p>Structured logging for all requests</p>
                    </div>
                    <div class="feature-card">
                        <h3>📊 Metrics</h3>
                        <p>Prometheus metrics for monitoring</p>
                    </div>
                    <div class="feature-card">
                        <h3>🔐 CORS</h3>
                        <p>Cross-origin request support</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🏗️ Architecture</h2>
                <div class="architecture">
┌─────────────────────────────────────────────────────┐
│          Client Requests (Browser, Mobile, API)     │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────▼────────────────────┐
        │  CloudGate API Gateway (8000)   │
        │  ├─ Rate Limiter                │
        │  ├─ Circuit Breaker             │
        │  ├─ Request Router              │
        │  └─ Logging Middleware          │
        └────────────┬─────────────────────┘
                     │
        ┌────────────┴──────────────────┐
        │                               │
    ┌───▼────────────────┐  ┌──────────▼────────┐
    │   Auth Service     │  │   Other Services  │
    │   (8001)           │  │   (Future)        │
    │  - Registration    │  │                   │
    │  - Login           │  │                   │
    │  - Token Mgmt      │  │                   │
    └────────────────────┘  └───────────────────┘
                </div>
            </div>

            <div class="section">
                <h2>🚀 Quick Start</h2>
                <ol>
                    <li><strong>Health Check:</strong> <code>GET /api/v1/health</code></li>
                    <li><strong>View Metrics:</strong> <code>GET /metrics</code></li>
                    <li><strong>Browse Docs:</strong> Visit <code>/docs</code> (Swagger UI)</li>
                    <li><strong>Test Endpoints:</strong> Use Swagger UI "Try it out" button</li>
                </ol>
            </div>

            <div class="section">
                <h2>📊 Monitoring & Observability</h2>
                <ul>
                    <li><strong>Prometheus Metrics:</strong> <code>/metrics</code> - Real-time metrics</li>
                    <li><strong>Health Check:</strong> <code>/api/v1/health</code> - Service status</li>
                    <li><strong>Grafana Dashboards:</strong> <a href="http://localhost:3000" target="_blank">http://localhost:3000</a></li>
                    <li><strong>Request Logging:</strong> Structured JSON logs for all requests</li>
                </ul>
            </div>

            <div class="section">
                <h2>🔌 Backend Services</h2>
                <ul>
                    <li><strong>Auth Service:</strong> <a href="http://localhost:8001" target="_blank">http://localhost:8001</a> - User authentication & JWT tokens</li>
                    <li><strong>Prometheus:</strong> <a href="http://localhost:9090" target="_blank">http://localhost:9090</a> - Metrics database</li>
                    <li><strong>Grafana:</strong> <a href="http://localhost:3000" target="_blank">http://localhost:3000</a> - Dashboards (admin/admin)</li>
                </ul>
            </div>

            <div class="section" style="margin-bottom: 0;">
                <h2>❓ Common Use Cases</h2>
                <ul>
                    <li><strong>Register User:</strong> <code>POST /api/v1/auth/register</code> (via gateway routing)</li>
                    <li><strong>Login:</strong> <code>POST /api/v1/auth/login</code> (via gateway routing)</li>
                    <li><strong>Get Profile:</strong> <code>GET /api/v1/auth/me</code> (requires token)</li>
                    <li><strong>Check Gateway Health:</strong> <code>GET /api/v1/health</code></li>
                    <li><strong>View Metrics:</strong> <code>GET /metrics</code> (Prometheus format)</li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
"""

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    config = get_gateway_config()
    uvicorn.run(
        "services.gateway.main:app",
        host="0.0.0.0",
        port=config.service_port,
        reload=config.debug,
    )
