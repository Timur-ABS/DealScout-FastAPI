from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://postgres:3557@localhost:5432/dealscout"

engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

metadata = MetaData()

from .models import deals, plans, reset_password, sessions, user, profit_days


# Создание таблиц при первом запуске
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
