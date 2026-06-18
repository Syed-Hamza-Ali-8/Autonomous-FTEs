#!/usr/bin/env python3
"""
Complete System Verification Script

Checks:
1. Environment variables
2. Database connection (Neon)
3. Redis connection
4. Groq API
5. Gmail integration
6. File structure
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

async def verify_system():
    print("="*70)
    print("🔍 CANDIDATE SCREENING AGENT - SYSTEM VERIFICATION")
    print("="*70)

    all_checks_passed = True

    # 1. Environment Variables
    print("\n📋 1. ENVIRONMENT VARIABLES")
    print("-" * 70)

    env_checks = {
        "Groq API": [
            ("OPENAI_API_KEY", True),
            ("OPENAI_BASE_URL", True),
            ("GROQ_MODEL", True),
        ],
        "Database": [
            ("DATABASE_URL", True),
            ("REDIS_URL", True),
        ],
        "Gmail": [
            ("GMAIL_CLIENT_ID", False),
            ("GMAIL_CLIENT_SECRET", False),
            ("GMAIL_REFRESH_TOKEN", False),
            ("JOBS_INBOX_EMAIL", False),
            ("HIRING_MANAGER_EMAIL", False),
        ],
        "App Settings": [
            ("DRY_RUN", True),
        ]
    }

    for category, vars in env_checks.items():
        print(f"\n{category}:")
        for var_name, required in vars:
            value = os.getenv(var_name)
            if not value or value.startswith('your_') or value.startswith('xai-your'):
                if required:
                    print(f"   ❌ {var_name}: Not configured (REQUIRED)")
                    all_checks_passed = False
                else:
                    print(f"   ⚠️  {var_name}: Not configured (optional for testing)")
            else:
                # Mask sensitive values
                if 'SECRET' in var_name or 'TOKEN' in var_name or 'KEY' in var_name:
                    display_value = value[:15] + "..." if len(value) > 15 else "***"
                else:
                    display_value = value[:50] + "..." if len(value) > 50 else value
                print(f"   ✅ {var_name}: {display_value}")

    # 2. Database Connection
    print("\n" + "="*70)
    print("🗄️  2. DATABASE CONNECTION (NEON)")
    print("-" * 70)

    try:
        from db.database import AsyncSessionLocal
        from db import crud

        async with AsyncSessionLocal() as db:
            jobs = await crud.get_all_jobs(db)
            print(f"   ✅ Connected to Neon PostgreSQL")
            print(f"   ✅ Tables accessible")
            print(f"   📊 Current jobs: {len(jobs)}")
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        all_checks_passed = False

    # 3. Redis Connection
    print("\n" + "="*70)
    print("📮 3. REDIS CONNECTION")
    print("-" * 70)

    try:
        import redis.asyncio as redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        r = redis.from_url(redis_url)
        await r.ping()
        print(f"   ✅ Connected to Redis")
        print(f"   📍 URL: {redis_url}")
        await r.close()
    except Exception as e:
        print(f"   ❌ Redis connection failed: {e}")
        print(f"   💡 Make sure Docker Compose is running: docker-compose up -d")
        all_checks_passed = False

    # 4. Groq API
    print("\n" + "="*70)
    print("🤖 4. GROQ API CONNECTION")
    print("-" * 70)

    try:
        from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled

        set_tracing_disabled(disabled=True)

        client = AsyncOpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_BASE_URL'),
        )

        model = OpenAIChatCompletionsModel(
            model=os.getenv('GROQ_MODEL'),
            openai_client=client,
        )

        agent = Agent(
            name='Test Agent',
            model=model,
            instructions='You are a helpful assistant. Respond with exactly: "System check passed"'
        )

        result = await Runner.run(agent, 'Respond with the exact phrase.')
        print(f"   ✅ Groq API connected")
        print(f"   🤖 Model: {os.getenv('GROQ_MODEL')}")
        print(f"   💬 Test response: {result.final_output[:50]}...")
    except Exception as e:
        print(f"   ❌ Groq API connection failed: {e}")
        all_checks_passed = False

    # 5. Gmail Integration
    print("\n" + "="*70)
    print("📧 5. GMAIL INTEGRATION")
    print("-" * 70)

    gmail_configured = all([
        os.getenv('GMAIL_CLIENT_ID') and not os.getenv('GMAIL_CLIENT_ID').startswith('your_'),
        os.getenv('GMAIL_CLIENT_SECRET') and not os.getenv('GMAIL_CLIENT_SECRET').startswith('your_'),
        os.getenv('GMAIL_REFRESH_TOKEN') and not os.getenv('GMAIL_REFRESH_TOKEN').startswith('your_'),
    ])

    if gmail_configured:
        try:
            from services.gmail_service import gmail_service

            dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'

            message_id = gmail_service.send_email(
                to=os.getenv('HIRING_MANAGER_EMAIL'),
                subject="System Verification Test",
                body="This is a test email from the system verification script."
            )

            print(f"   ✅ Gmail service initialized")
            print(f"   📧 Jobs inbox: {os.getenv('JOBS_INBOX_EMAIL')}")
            print(f"   👤 Hiring manager: {os.getenv('HIRING_MANAGER_EMAIL')}")
            print(f"   🔒 DRY_RUN mode: {'Enabled (safe)' if dry_run else 'Disabled (real emails)'}")

            if dry_run:
                print(f"   ✅ Test email logged (DRY_RUN mode)")
            else:
                print(f"   ✅ Test email sent successfully")
        except Exception as e:
            print(f"   ❌ Gmail integration failed: {e}")
            all_checks_passed = False
    else:
        print(f"   ⚠️  Gmail not configured (optional for testing)")
        print(f"   💡 Run: uv run python authenticate_gmail.py")

    # 6. File Structure
    print("\n" + "="*70)
    print("📁 6. FILE STRUCTURE")
    print("-" * 70)

    required_files = [
        ("backend/db/models.py", "Database models"),
        ("backend/screening_agent.py", "AI screening agent"),
        ("backend/main.py", "FastAPI application"),
        ("backend/orchestrator.py", "Queue orchestrator"),
        ("rubrics/Senior_Backend_Engineer.md", "Sample rubric"),
        ("frontend/package.json", "Frontend config"),
    ]

    for file_path, description in required_files:
        full_path = os.path.join("..", file_path) if not file_path.startswith("backend/") else file_path
        if os.path.exists(full_path):
            print(f"   ✅ {description}: {file_path}")
        else:
            print(f"   ❌ {description}: {file_path} (missing)")
            all_checks_passed = False

    # Final Summary
    print("\n" + "="*70)
    print("📊 VERIFICATION SUMMARY")
    print("="*70)

    if all_checks_passed:
        print("\n✅ ALL CRITICAL CHECKS PASSED!")
        print("\n🚀 You can now start the application:")
        print("   Terminal 1: cd backend && uv run uvicorn main:app --reload")
        print("   Terminal 2: cd frontend && npm run dev")
        print("\n🌐 Access the dashboard at: http://localhost:3000")
    else:
        print("\n⚠️  SOME CHECKS FAILED")
        print("\n📝 Please fix the issues above before starting the application.")
        print("\n💡 Common fixes:")
        print("   - Groq API: Check OPENAI_API_KEY in .env")
        print("   - Database: Verify DATABASE_URL connection string")
        print("   - Redis: Run 'docker-compose up -d'")
        print("   - Gmail: Run 'uv run python authenticate_gmail.py'")

    print("\n" + "="*70)
    return all_checks_passed

if __name__ == '__main__':
    result = asyncio.run(verify_system())
    sys.exit(0 if result else 1)
