from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from shared.config import BaseConfig


class Base(DeclarativeBase):
    pass


class DatabaseManager:
    def __init__(self, config: BaseConfig) -> None:
        self.config = config
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            # Use NullPool for testing, regular pool for production
            pool_class = NullPool if self.config.app_env == "testing" else None

            self._engine = create_async_engine(
                self.config.database_url,
                echo=self.config.debug,
                pool_size=(
                    self.config.database_pool_size if pool_class is None else None
                ),
                max_overflow=(
                    self.config.database_max_overflow if pool_class is None else None
                ),
                poolclass=pool_class,
                future=True,
            )

            # Log slow queries in development
            if self.config.debug:

                @event.listens_for(self._engine.sync_engine, "before_cursor_execute")
                def receive_before_cursor_execute(
                    conn: Any,
                    cursor: Any,
                    statement: Any,
                    parameters: Any,
                    context: Any,
                    executemany: Any,
                ) -> None:
                    conn.info.setdefault("query_start_time", []).append(
                        __import__("time").time()
                    )

                @event.listens_for(self._engine.sync_engine, "after_cursor_execute")
                def receive_after_cursor_execute(
                    conn: Any,
                    cursor: Any,
                    statement: Any,
                    parameters: Any,
                    context: Any,
                    executemany: Any,
                ) -> None:
                    total = (
                        __import__("time").time() - conn.info["query_start_time"].pop()
                    )
                    if total > 0.1:  # Log queries taking more than 100ms
                        import structlog

                        logger = structlog.get_logger()
                        logger.warning(
                            "Slow query detected",
                            duration_ms=round(total * 1000, 2),
                            statement=statement[:200],
                        )

        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
        return self._session_factory

    async def get_session(self) -> AsyncGenerator[AsyncSession]:
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self) -> None:
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    async def health_check(self) -> dict[str, Any]:
        try:
            async with self.session() as session:
                await session.execute(__import__("sqlalchemy").text("SELECT 1"))
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


# Module-level database manager instance (to be initialized per service)
_db_manager: DatabaseManager | None = None


def init_database(config: BaseConfig) -> DatabaseManager:
    global _db_manager
    _db_manager = DatabaseManager(config)
    return _db_manager


def get_database() -> DatabaseManager:
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database first.")
    return _db_manager
