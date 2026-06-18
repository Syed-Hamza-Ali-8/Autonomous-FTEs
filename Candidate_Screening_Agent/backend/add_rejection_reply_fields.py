"""
Database migration: Add rejection reply tracking fields to candidates table.

Adds:
- rejection_message_id: Tracks the Gmail message ID of the rejection email
- rejection_reply_count: Counts how many times we've responded to rejection replies (max 3)
"""
import asyncio
from sqlalchemy import text
from db.database import engine


async def migrate():
    """Add rejection reply tracking fields to candidates table."""
    async with engine.begin() as conn:
        # Check if columns already exist
        result = await conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='candidates'
            AND column_name IN ('rejection_message_id', 'rejection_reply_count')
        """))
        existing_columns = [row[0] for row in result]

        # Add rejection_message_id if it doesn't exist
        if 'rejection_message_id' not in existing_columns:
            print("Adding rejection_message_id column...")
            await conn.execute(text("""
                ALTER TABLE candidates
                ADD COLUMN rejection_message_id VARCHAR(200)
            """))
            print("✓ Added rejection_message_id column")
        else:
            print("✓ rejection_message_id column already exists")

        # Add rejection_reply_count if it doesn't exist
        if 'rejection_reply_count' not in existing_columns:
            print("Adding rejection_reply_count column...")
            await conn.execute(text("""
                ALTER TABLE candidates
                ADD COLUMN rejection_reply_count INTEGER DEFAULT 0
            """))
            print("✓ Added rejection_reply_count column")
        else:
            print("✓ rejection_reply_count column already exists")

        print("\n✅ Migration completed successfully!")


if __name__ == "__main__":
    print("Running database migration for rejection reply tracking...\n")
    asyncio.run(migrate())
