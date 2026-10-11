from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


class Database:
    def __init__(self, url: str):
        # Local migration login owns the schema; runtime always assumes the restricted role.
        self.engine = create_async_engine(
            make_url(url).set(drivername="postgresql+asyncpg"),
            pool_pre_ping=True, hide_parameters=True,
            connect_args={"timeout": 2,
                          "server_settings": {"role": "app_rw", "statement_timeout": "5000"}},
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    @asynccontextmanager
    async def transaction(self, workspace_id: UUID):
        async with self.sessions.begin() as session:
            await session.execute(
                text("SELECT set_config('app.workspace_id', :workspace, true)"),
                {"workspace": str(workspace_id)},
            )
            yield session

    @asynccontextmanager
    async def identity_transaction(self, user_id: UUID):
        async with self.sessions.begin() as session:
            await session.execute(text("SELECT set_config('app.actor_id', :actor, true)"),
                                  {"actor": str(user_id)})
            yield session

    async def ready(self) -> None:
        async with self.engine.connect() as connection:
            result = await connection.execute(
                text("SELECT version_num FROM public.alembic_version")
            )
            if result.scalar_one_or_none() is None:
                raise RuntimeError("Foundation migration is missing.")

    async def close(self) -> None:
        await self.engine.dispose()
