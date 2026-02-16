"""
Database Configuration and Connection Management
Phase 2: Specialization
"""

import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://fte_user:fte_password@localhost:5432/customer_success_fte"
)

# Create async engine
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("ENVIRONMENT") == "development",
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    poolclass=NullPool if os.getenv("ENVIRONMENT") == "test" else None
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context():
    """
    Context manager for database session.

    Usage:
        async with get_db_context() as db:
            result = await db.execute(query)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database (create tables if they don't exist)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    await engine.dispose()


# Health check
async def check_db_health() -> bool:
    """Check if database is accessible."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            return True
    except Exception:
        return False
