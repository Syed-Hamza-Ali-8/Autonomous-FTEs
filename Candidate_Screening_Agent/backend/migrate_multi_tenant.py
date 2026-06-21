"""
Migration script: adds multi-tenant support to existing database.
Run: cd backend && uv run python migrate_multi_tenant.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from db.database import engine, AsyncSessionLocal, init_db


async def run_migration():
    print("🔄 Starting multi-tenant migration...")

    await init_db()
    print("  ✅ Tables created")

    async with AsyncSessionLocal() as session:
        # Check if already migrated
        result = await session.execute(text("SELECT COUNT(*) FROM companies"))
        if result.scalar() > 0:
            print("  ⏭️  Already migrated")
            return

        # 1. Add company_id columns via ALTER TABLE
        print("  1. Adding company_id columns...")
        for table_name in ["jobs", "candidates", "pending_approvals",
                          "interview_slots", "scheduling_conversations", "audit_log"]:
            try:
                await session.execute(text(
                    f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS company_id INTEGER"
                ))
                await session.commit()
                print(f"  ✅ {table_name}")
            except Exception as e:
                print(f"  ⚠️  {table_name}: {e}")
                try:
                    await session.rollback()
                except Exception:
                    pass

        # 2. Create default company
        print("  2. Creating default company...")
        await session.execute(text(
            "INSERT INTO companies (name, slug, plan, is_active) VALUES ('Demo Company', 'demo-company', 'free', true)"
        ))
        await session.commit()

        cid_result = await session.execute(text("SELECT id FROM companies WHERE slug = 'demo-company'"))
        cid = cid_result.scalar()
        print(f"  ✅ Default company (id={cid})")

        # 3. Assign existing data
        print("  3. Migrating existing data...")
        for table_name in ["jobs", "candidates", "pending_approvals",
                          "interview_slots", "scheduling_conversations", "audit_log"]:
            try:
                result = await session.execute(
                    text(f"UPDATE {table_name} SET company_id = :cid WHERE company_id IS NULL"),
                    {"cid": cid},
                )
                await session.commit()
                print(f"  ✅ {table_name}: {result.rowcount} rows")
            except Exception as e:
                print(f"  ⚠️  {table_name}: {e}")
                try:
                    await session.rollback()
                except Exception:
                    pass

        # 4. Create default admin user
        print("  4. Creating default admin user...")
        import bcrypt
        pw_hash = bcrypt.hashpw(b"demo1234", bcrypt.gensalt(rounds=12)).decode("utf-8")
        await session.execute(text(
            "INSERT INTO users (company_id, email, password_hash, name, role, is_active) "
            "VALUES (:cid, 'admin@demo.com', :pw, 'Demo Admin', 'company_admin', true)"
        ), {"cid": cid, "pw": pw_hash})
        await session.commit()
        print("  ✅ admin@demo.com / demo1234")

    print("\n🎉 Migration complete!")
    print("   Login: admin@demo.com / demo1234")


if __name__ == "__main__":
    asyncio.run(run_migration())
