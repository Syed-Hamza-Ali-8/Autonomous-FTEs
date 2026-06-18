"""Reset database - drop all tables and recreate with new schema."""
import asyncio
from db.database import engine
from db.models import Base
from dotenv import load_dotenv

load_dotenv()


async def reset_database():
    """Drop all tables and recreate them."""
    print("=" * 70)
    print("🔄 Resetting Database")
    print("=" * 70)

    print("\n⚠️  Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("✅ All tables dropped")

    print("\n📋 Creating tables with new schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ All tables created")

    print("\n" + "=" * 70)
    print("✅ Database reset complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(reset_database())
