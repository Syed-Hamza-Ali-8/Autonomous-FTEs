#!/usr/bin/env python3
"""
Test script to demonstrate the Candidate Screening Agent workflow.

This script simulates the complete workflow:
1. Creates a test candidate with CV
2. Triggers AI scoring
3. Generates screening questions
4. Simulates candidate reply
5. Creates pending approval
6. Shows how to approve/reject

Usage:
    python test_workflow.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from db.database import AsyncSessionLocal
from db import crud
from screening_agent import score_candidate, generate_screening_questions, analyze_reply
from orchestrator import process_new_candidate, process_candidate_reply


async def main():
    """Run the complete workflow test."""

    print("=" * 80)
    print("CANDIDATE SCREENING AGENT - WORKFLOW TEST")
    print("=" * 80)
    print()

    # Sample CV text
    cv_text = """
    John Doe
    Senior Software Engineer
    john.doe@example.com | +1-555-0123 | linkedin.com/in/johndoe

    SUMMARY
    Highly skilled Senior Backend Engineer with 8+ years of experience building
    scalable distributed systems. Expert in Python, FastAPI, PostgreSQL, Redis,
    and microservices architecture. Led teams of 5-8 engineers and architected
    systems handling 10M+ requests per day.

    EXPERIENCE

    Senior Backend Engineer | TechCorp Inc. | 2020 - Present
    - Architected and built microservices platform serving 5M+ users
    - Designed RESTful APIs using FastAPI and async Python
    - Optimized PostgreSQL queries, reducing response time by 60%
    - Implemented Redis caching strategy, improving throughput by 3x
    - Led migration from monolith to microservices architecture
    - Mentored 3 junior engineers and conducted code reviews

    Backend Engineer | StartupXYZ | 2018 - 2020
    - Built real-time data processing pipeline using Kafka and Python
    - Designed database schema for multi-tenant SaaS application
    - Implemented OAuth2 authentication and authorization
    - Wrote comprehensive unit and integration tests (95% coverage)
    - Deployed services to AWS using Docker and Kubernetes

    Software Engineer | DevShop | 2016 - 2018
    - Developed Django REST APIs for e-commerce platform
    - Integrated payment gateways (Stripe, PayPal)
    - Optimized database queries and added proper indexing
    - Participated in agile development and sprint planning

    TECHNICAL SKILLS
    - Languages: Python (expert), Go (proficient), JavaScript (familiar)
    - Frameworks: FastAPI, Django, Flask, Express.js
    - Databases: PostgreSQL, MySQL, MongoDB, Redis
    - Message Queues: Kafka, RabbitMQ, Redis Streams
    - Cloud: AWS (EC2, RDS, S3, Lambda), Docker, Kubernetes
    - Tools: Git, CI/CD, Prometheus, Grafana, ELK Stack

    EDUCATION
    B.S. Computer Science | University of Technology | 2016

    ACHIEVEMENTS
    - Open source contributor to FastAPI and SQLAlchemy
    - Speaker at PyCon 2023: "Building High-Performance APIs"
    - Technical blog with 10K+ monthly readers
    """

    async with AsyncSessionLocal() as db:
        # Step 1: Create candidate
        print("Step 1: Creating test candidate...")
        print("-" * 80)

        candidate = await crud.create_candidate(
            db=db,
            job_id=1,
            email="john.doe@example.com",
            name="John Doe",
            cv_text=cv_text,
            gmail_message_id="test_message_123"
        )

        print(f"✓ Created candidate ID: {candidate.id}")
        print(f"  Name: {candidate.name}")
        print(f"  Email: {candidate.email}")
        print(f"  Status: {candidate.status}")
        print()

        # Step 2: Score candidate
        print("Step 2: Scoring candidate with AI...")
        print("-" * 80)

        try:
            score_data = await score_candidate(
                cv_text=cv_text,
                rubric_path="rubrics/Senior_Backend_Engineer.md"
            )

            print(f"✓ Candidate scored successfully!")
            print(f"  Total Score: {score_data.get('total_score')}/100")
            print(f"  Must-Haves Met: {score_data.get('must_haves_met')}")
            print(f"  Recommendation: {score_data.get('recommendation')}")
            print(f"  Confidence: {score_data.get('confidence')}")
            print()

            if score_data.get('strengths'):
                print("  Strengths:")
                for strength in score_data.get('strengths', [])[:3]:
                    print(f"    • {strength}")
                print()

            if score_data.get('weaknesses'):
                print("  Weaknesses:")
                for weakness in score_data.get('weaknesses', [])[:3]:
                    print(f"    • {weakness}")
                print()

            # Update candidate with score
            await crud.update_candidate_score(db, candidate.id, score_data)

        except Exception as e:
            print(f"✗ Error scoring candidate: {e}")
            print("  Note: Make sure OPENAI_API_KEY is set in .env")
            return

        # Step 3: Generate screening questions
        print("Step 3: Generating screening questions...")
        print("-" * 80)

        try:
            questions = await generate_screening_questions(
                cv_text=cv_text,
                rubric_path="rubrics/Senior_Backend_Engineer.md"
            )

            print(f"✓ Generated {len(questions)} screening questions:")
            for i, question in enumerate(questions, 1):
                print(f"  {i}. {question}")
            print()

            # Update candidate with questions
            await crud.update_candidate_questions(db, candidate.id, questions)
            await crud.update_candidate_status(db, candidate.id, "awaiting_reply")

        except Exception as e:
            print(f"✗ Error generating questions: {e}")
            return

        # Step 4: Simulate candidate reply
        print("Step 4: Simulating candidate reply...")
        print("-" * 80)

        reply_text = """
        Thank you for the opportunity to answer these questions!

        1. Regarding distributed systems: I've built several microservices platforms
        at TechCorp. The biggest challenge was handling eventual consistency across
        services. We solved this using event sourcing with Kafka and implemented
        the Saga pattern for distributed transactions. We also used circuit breakers
        to prevent cascading failures.

        2. For API design, I prioritize: (1) Clear resource naming and RESTful
        conventions, (2) Proper HTTP status codes and error responses, (3) Versioning
        strategy (URL-based for major versions), (4) Rate limiting and authentication,
        (5) Comprehensive OpenAPI documentation, and (6) Backward compatibility.

        3. The most complex performance issue was a memory leak in our Python service.
        I used memory_profiler and objgraph to identify that SQLAlchemy sessions
        weren't being properly closed. I implemented proper session management with
        context managers and added monitoring with Prometheus to track memory usage.

        4. For code quality, I enforce: (1) Comprehensive code reviews with at least
        2 approvers, (2) 80%+ test coverage requirement, (3) Pre-commit hooks for
        linting (black, flake8, mypy), (4) CI/CD pipeline that runs all tests, and
        (5) Regular refactoring sessions to address technical debt.

        5. Database optimization strategies I've used: (1) Proper indexing based on
        query patterns, (2) Query analysis with EXPLAIN ANALYZE, (3) Connection
        pooling with pgbouncer, (4) Read replicas for read-heavy workloads, (5)
        Materialized views for complex aggregations, and (6) Partitioning for
        large tables.

        I'm very excited about this opportunity and would love to discuss further!
        """

        print("✓ Simulated candidate reply (see above)")
        print()

        # Step 5: Analyze reply
        print("Step 5: Analyzing reply with AI...")
        print("-" * 80)

        try:
            original_score = {
                "total_score": score_data.get("total_score"),
                "recommendation": score_data.get("recommendation")
            }

            analysis = await analyze_reply(
                questions=questions,
                reply_text=reply_text,
                original_score=original_score
            )

            print(f"✓ Reply analyzed successfully!")
            print(f"  Final Score: {analysis.get('final_score')}/100")
            print(f"  Updated Recommendation: {analysis.get('updated_recommendation')}")
            print()

            if analysis.get('brief_summary'):
                print(f"  Summary: {analysis.get('brief_summary')}")
                print()

            # Update candidate with reply
            await crud.update_candidate_reply(db, candidate.id, reply_text, analysis)

        except Exception as e:
            print(f"✗ Error analyzing reply: {e}")
            return

        # Step 6: Create pending approval
        print("Step 6: Creating pending approval...")
        print("-" * 80)

        approval = await crud.create_pending_approval(
            db=db,
            candidate_id=candidate.id,
            job_id=1,
            action="advance",
            score=analysis.get("final_score"),
            recommendation=analysis.get("updated_recommendation"),
            brief_summary=analysis.get("brief_summary")
        )

        await crud.update_candidate_status(db, candidate.id, "shortlisted")

        print(f"✓ Created pending approval ID: {approval.id}")
        print(f"  Action: {approval.action}")
        print(f"  Score: {approval.score}/100")
        print()

        # Step 7: Show next steps
        print("=" * 80)
        print("WORKFLOW COMPLETE!")
        print("=" * 80)
        print()
        print("Next Steps:")
        print()
        print("1. View candidate in web UI:")
        print(f"   http://localhost:3000/candidates/{candidate.id}")
        print()
        print("2. View pending approval:")
        print("   http://localhost:3000/approvals")
        print()
        print("3. Approve via API:")
        print(f"   curl -X POST http://localhost:8000/api/approvals/{approval.id}/approve")
        print()
        print("4. Or reject via API:")
        print(f"   curl -X POST http://localhost:8000/api/approvals/{approval.id}/reject")
        print()
        print("5. View all candidates:")
        print("   http://localhost:3000/candidates")
        print()
        print("6. View job details:")
        print("   http://localhost:3000/jobs/1")
        print()
        print("=" * 80)
        print()
        print("✓ Test completed successfully!")
        print()
        print("Note: DRY_RUN=true is enabled, so no actual emails were sent.")
        print("      All email actions are logged only.")
        print()


if __name__ == "__main__":
    asyncio.run(main())
