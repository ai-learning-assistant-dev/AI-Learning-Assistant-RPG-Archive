import asyncpg

from config.settings import settings


class StoreService:
    """
    Service for managing PostgreSQL database connections.
    dsn : postgres://user:pass@host:port/database
    """

    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def init(self):
        dsn = f"postgresql://{settings.pg_user}:{settings.pg_password}@{settings.pg_host}:{settings.pg_port}/{settings.pg_database}"
        self.pool = await asyncpg.create_pool(dsn=dsn)

    async def close(self):
        if self.pool is not None:
            await self.pool.close()


store_service = StoreService()
