"""Migration: Add description and services columns to companies table."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/screening_db")
# Convert for asyncpg direct connection
DIRECT_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


async def migrate():
    conn = await asyncpg.connect(DIRECT_URL)
    try:
        # Check if columns already exist
        cols = await conn.fetch("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'companies' AND column_name IN ('description', 'services')
        """)
        existing = {c["column_name"] for c in cols}

        if "description" not in existing:
            await conn.execute("ALTER TABLE companies ADD COLUMN description TEXT")
            print("Added column: companies.description")
        else:
            print("Column companies.description already exists")

        if "services" not in existing:
            await conn.execute("ALTER TABLE companies ADD COLUMN services VARCHAR(300)")
            print("Added column: companies.services")
        else:
            print("Column companies.services already exists")

        print("Migration complete!")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
