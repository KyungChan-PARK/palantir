import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from palantir.auth.models import Base

async def init_db():
    engine = create_async_engine("sqlite+aiosqlite:///./users.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db()) 