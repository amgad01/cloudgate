import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.config import AuthConfig, GatewayConfig
from shared.database.connection import Base

TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'

def pytest_collection_modifyitems(config, items):
    import importlib

    import pytest as _pytest
    has_aiosqlite = importlib.util.find_spec('aiosqlite') is not None
    if not has_aiosqlite:
        for item in items:
            if 'tests/integration' in str(item.fspath):
                item.add_marker(_pytest.mark.skip(reason='aiosqlite not installed - skipping integration tests'))

@pytest.fixture(scope='session')
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope='session')
def auth_config() -> AuthConfig:
    return AuthConfig(app_env='testing', debug=True, database_url=TEST_DATABASE_URL, redis_url='redis://localhost:6379/0', jwt_secret_key='test-jwt-secret-key', secret_key='test-secret-key')

@pytest.fixture(scope='session')
def gateway_config() -> GatewayConfig:
    return GatewayConfig(app_env='testing', debug=True, redis_url='redis://localhost:6379/0', auth_service_url='http://localhost:8001', user_service_url='http://localhost:8002', analytics_service_url='http://localhost:8003', jwt_secret_key='test-jwt-secret-key', secret_key='test-secret-key')

@pytest_asyncio.fixture(scope='function')
async def db_engine(auth_config: AuthConfig):
    engine = create_async_engine(auth_config.database_url, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture(scope='function')
async def db_session(db_engine) -> AsyncGenerator[AsyncSession]:
    session_factory = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False)
    async with session_factory() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture(scope='function')
async def auth_client(auth_config: AuthConfig, db_engine) -> AsyncGenerator[AsyncClient]:
    from services.auth.main import create_app
    from shared.database.connection import init_database
    from shared.database.redis import init_redis
    init_database(auth_config)
    init_redis(auth_config)
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        yield client

@pytest_asyncio.fixture(scope='function')
async def gateway_client(gateway_config: GatewayConfig) -> AsyncGenerator[AsyncClient]:
    from services.gateway.main import create_app
    from shared.database.redis import init_redis
    init_redis(gateway_config)
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        yield client
