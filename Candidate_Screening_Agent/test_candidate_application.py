#!/usr/bin/env python3
"""
Test the candidate application workflow via API.

This script simulates a candidate submitting their application through the web form.
"""

import asyncio
import sys
from pathlib import Path
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))


def create_test_resume_pdf() -> bytes:
    """Create a test PDF resume."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Add content to PDF
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Jane Smith")

    c.setFont("Helvetica", 12)
    c.drawString(100, 730, "Senior Full-Stack Engineer")
    c.drawString(100, 710, "jane.smith@example.com | +1-555-9876")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 680, "SUMMARY")
    c.setFont("Helvetica", 11)

    summary = """
    Experienced Full-Stack Engineer with 10+ years building scalable web applications.
    Expert in Python, FastAPI, React, TypeScript, PostgreSQL, and cloud infrastructure.
    Led teams of 8+ engineers and architected systems serving 20M+ users.
    """

    y = 660
    for line in summary.strip().split('\n'):
        c.drawString(100, y, line.strip())
        y -= 15

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, y - 10, "EXPERIENCE")
    c.setFont("Helvetica", 11)

    experience = """
    Lead Engineer | TechGiant Corp | 2020 - Present
    - Architected microservices platform serving 20M+ users with 99.99% uptime
    - Built real-time analytics dashboard using React, TypeScript, and WebSockets
    - Designed PostgreSQL database schema with advanced indexing and partitioning
    - Implemented CI/CD pipeline reducing deployment time by 80%
    - Mentored 5 junior engineers and conducted technical interviews

    Senior Backend Engineer | StartupCo | 2017 - 2020
    - Developed RESTful APIs using FastAPI and async Python
    - Optimized database queries reducing response time by 70%
    - Implemented Redis caching strategy improving throughput by 5x
    - Built event-driven architecture using Kafka and RabbitMQ
    - Wrote comprehensive tests achieving 95% code coverage

    Software Engineer | DevShop Inc | 2014 - 2017
    - Built e-commerce platform using Django and React
    - Integrated payment gateways (Stripe, PayPal, Square)
    - Implemented OAuth2 authentication and JWT tokens
    - Deployed applications to AWS using Docker and Kubernetes
    """

    y -= 30
    for line in experience.strip().split('\n'):
        if y < 100:
            c.showPage()
            y = 750
        c.drawString(100, y, line.strip()[:80])
        y -= 15

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, y - 10, "TECHNICAL SKILLS")
    c.setFont("Helvetica", 11)

    skills = """
    Languages: Python (expert), TypeScript (expert), JavaScript, Go
    Backend: FastAPI, Django, Flask, Node.js, Express
    Frontend: React, Next.js, Vue.js, Tailwind CSS
    Databases: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch
    Cloud: AWS (EC2, RDS, S3, Lambda, CloudFront), Docker, Kubernetes
    Message Queues: Kafka, RabbitMQ, Redis Streams, AWS SQS
    Tools: Git, CI/CD, Prometheus, Grafana, ELK Stack, Terraform
    """

    y -= 30
    for line in skills.strip().split('\n'):
        if y < 100:
            c.showPage()
            y = 750
        c.drawString(100, y, line.strip())
        y -= 15

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, y - 10, "EDUCATION")
    c.setFont("Helvetica", 11)
    c.drawString(100, y - 30, "M.S. Computer Science | Stanford University | 2014")
    c.drawString(100, y - 45, "B.S. Computer Science | MIT | 2012")

    c.save()
    buffer.seek(0)
    return buffer.read()


async def test_application_submission():
    """Test submitting a candidate application."""
    import aiohttp

    print("=" * 80)
    print("TESTING CANDIDATE APPLICATION SUBMISSION")
    print("=" * 80)
    print()

    # Create test PDF resume
    print("Step 1: Creating test PDF resume...")
    pdf_bytes = create_test_resume_pdf()
    print(f"✓ Created PDF resume ({len(pdf_bytes)} bytes)")
    print()

    # Submit application
    print("Step 2: Submitting application via API...")

    form_data = aiohttp.FormData()
    form_data.add_field('name', 'Jane Smith')
    form_data.add_field('email', 'jane.smith@example.com')
    form_data.add_field('job_id', '1')
    form_data.add_field('resume', pdf_bytes, filename='jane_smith_resume.pdf', content_type='application/pdf')

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:8000/api/applications/submit', data=form_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✓ Application submitted successfully!")
                    print(f"  Candidate ID: {result['candidate_id']}")
                    print(f"  Status: {result['status']}")
                    print(f"  Message: {result['message']}")
                    print()

                    candidate_id = result['candidate_id']

                    # Wait a moment for processing
                    print("Step 3: Waiting for AI processing...")
                    await asyncio.sleep(3)
                    print()

                    # Check application status
                    print("Step 4: Checking application status...")
                    async with session.get(f'http://localhost:8000/api/applications/status/{candidate_id}?email=jane.smith@example.com') as status_response:
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            print("✓ Application status retrieved:")
                            print(f"  Name: {status_data['name']}")
                            print(f"  Email: {status_data['email']}")
                            print(f"  Job: {status_data['job_title']}")
                            print(f"  Status: {status_data['status']}")
                            print(f"  Status Message: {status_data['status_message']}")
                            if status_data.get('total_score'):
                                print(f"  Score: {status_data['total_score']}/100")
                            print()
                        else:
                            error = await status_response.text()
                            print(f"✗ Failed to get status: {error}")
                            print()

                    # Get full candidate details
                    print("Step 5: Getting full candidate details...")
                    async with session.get(f'http://localhost:8000/api/candidates/{candidate_id}') as candidate_response:
                        if candidate_response.status == 200:
                            candidate_data = await candidate_response.json()
                            print("✓ Candidate details:")
                            print(f"  ID: {candidate_data['id']}")
                            print(f"  Name: {candidate_data['name']}")
                            print(f"  Email: {candidate_data['email']}")
                            print(f"  Status: {candidate_data['status']}")
                            print(f"  Total Score: {candidate_data.get('total_score', 'Not scored yet')}")
                            print(f"  Recommendation: {candidate_data.get('recommendation', 'Pending')}")
                            print()

                            if candidate_data.get('strengths'):
                                print("  Strengths:")
                                for strength in candidate_data['strengths'][:3]:
                                    print(f"    • {strength}")
                                print()

                            if candidate_data.get('screening_questions'):
                                print(f"  Screening Questions: {len(candidate_data['screening_questions'])} generated")
                                print()
                        else:
                            error = await candidate_response.text()
                            print(f"✗ Failed to get candidate details: {error}")
                            print()

                    print("=" * 80)
                    print("TEST COMPLETED SUCCESSFULLY!")
                    print("=" * 80)
                    print()
                    print("Next Steps:")
                    print()
                    print("1. View candidate in web UI:")
                    print(f"   http://localhost:3000/candidates/{candidate_id}")
                    print()
                    print("2. View application form:")
                    print("   http://localhost:3000/apply/1")
                    print()
                    print("3. View all jobs:")
                    print("   http://localhost:3000/jobs")
                    print()
                    print("4. Check pending approvals:")
                    print("   http://localhost:3000/approvals")
                    print()

                else:
                    error = await response.text()
                    print(f"✗ Application submission failed: {error}")
                    print()

    except Exception as e:
        print(f"✗ Error: {e}")
        print()
        print("Make sure the backend is running:")
        print("  cd backend && uv run uvicorn main:app --reload")
        print()


if __name__ == "__main__":
    asyncio.run(test_application_submission())
