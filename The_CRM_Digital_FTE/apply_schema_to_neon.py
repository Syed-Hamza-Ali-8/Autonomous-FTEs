#!/usr/bin/env python3
"""
Apply database schema to Neon.tech
"""
import psycopg2
import sys

# Neon.tech connection string
NEON_URL = "postgresql://neondb_owner:npg_PdN2KIxpOA3V@ep-withered-forest-ai7kjzjc-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"

def main():
    print("=" * 60)
    print("Applying Schema to Neon.tech Database")
    print("=" * 60)

    try:
        # Connect to Neon.tech
        print("\n1. Connecting to Neon.tech...")
        conn = psycopg2.connect(NEON_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        print("   ✅ Connected successfully!")

        # Read schema file
        print("\n2. Reading schema file...")
        with open('src/database/schema.sql', 'r') as f:
            schema_sql = f.read()
        print(f"   ✅ Schema file loaded ({len(schema_sql)} characters)")

        # Apply schema
        print("\n3. Applying schema to Neon.tech...")
        cursor.execute(schema_sql)
        print("   ✅ Schema applied successfully!")

        # Verify tables
        print("\n4. Verifying tables created...")
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()

        if tables:
            print(f"   ✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"      - {table[0]}")
        else:
            print("   ⚠️  No tables found!")

        # Check indexes
        print("\n5. Verifying indexes...")
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY indexname;
        """)
        indexes = cursor.fetchall()
        print(f"   ✅ Found {len(indexes)} indexes")

        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("✅ Schema successfully applied to Neon.tech!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
