from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine  # Sync engine for Alembic
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get DB URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set in your .env file.")

# ✅ Async Engine (for FastAPI runtime use)
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ✅ Sync Engine (for Alembic migrations)
# Alembic does not work with async engine, so we need a sync one
sync_engine = create_engine(DATABASE_URL.replace("postgresql+asyncpg", "postgresql"), echo=True)


# Dependency for FastAPI
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Async DB initializer (optional for runtime init, not used by Alembic)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
