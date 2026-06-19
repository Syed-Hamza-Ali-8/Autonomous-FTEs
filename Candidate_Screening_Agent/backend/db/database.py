from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
import os
import secrets
from db.models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/screening_db")

# Create async engine
# SQLite (used in tests) does not support pool_size/max_overflow
_is_sqlite = "sqlite" in DATABASE_URL
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    **({"pool_size": 10, "max_overflow": 20, "pool_pre_ping": True} if not _is_sqlite else {"pool_pre_ping": True}),
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


_jwt_secret: str | None = None

def get_jwt_secret() -> str:
    """Get the JWT secret from env, or generate one for dev mode (cached)."""
    global _jwt_secret
    if _jwt_secret is not None:
        return _jwt_secret
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        secret = secrets.token_hex(32)
        print("WARNING: JWT_SECRET_KEY not set. Using generated key (tokens will invalidate on restart).")
    _jwt_secret = secret
    return _jwt_secret


async def get_db():
    """Dependency for FastAPI to get database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Initialize database by creating all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
