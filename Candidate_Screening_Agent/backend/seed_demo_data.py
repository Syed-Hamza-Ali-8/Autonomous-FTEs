"""Seed the database with realistic demo data for showcasing the app."""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(__file__))

from db.models import Base, Job, Candidate, PendingApproval
from db.database import engine, AsyncSessionLocal


DEMO_JOBS = [
    {
        "title": "Senior Frontend Engineer",
        "slug": "senior-frontend-engineer",
        "description": "We're looking for a senior frontend engineer with deep React/Next.js experience to lead our product team.",
        "rubric_path": "rubrics/frontend_engineer.md",
        "hiring_manager_email": "sarah@techcorp.io",
    },
    {
        "title": "ML Platform Engineer",
        "slug": "ml-platform-engineer",
        "description": "Build and maintain the ML infrastructure that powers our AI screening agent. Python, PyTorch, and cloud-native experience required.",
        "rubric_path": "rubrics/ml_engineer.md",
        "hiring_manager_email": "marcus@techcorp.io",
    },
    {
        "title": "Product Designer",
        "slug": "product-designer",
        "description": "Shape the user experience of our platform. Strong portfolio in SaaS design and design systems required.",
        "rubric_path": "rubrics/product_designer.md",
        "hiring_manager_email": "luna@techcorp.io",
    },
]

DEMO_CANDIDATES = [
    # Senior Frontend Engineer candidates — spread across pipeline stages
    {
        "job_slug": "senior-frontend-engineer",
        "email": "alex.chen@gmail.com",
        "name": "Alex Chen",
        "status": "queued",
        "cv_text": "Senior Frontend Developer with 7+ years of experience building scalable web applications.\n\nEXPERIENCE\n• Senior Developer at Stripe — Led redesign of merchant dashboard, improving NPS by 23pts\n• Developer at Shopify — Built component library used across 12 product teams\n• Engineer at Airbnb — Developed real-time search filtering system\n\nSKILLS\nReact, TypeScript, Next.js, GraphQL, Tailwind CSS, Node.js\n\nEDUCATION\nB.S. Computer Science, Stanford University",
    },
    {
        "job_slug": "senior-frontend-engineer",
        "email": "maria.santos@outlook.com",
        "name": "Maria Santos",
        "status": "scoring",
        "cv_text": "Full-stack developer specializing in modern JavaScript frameworks.\n\nEXPERIENCE\n• Lead Developer at Vercel — Built internal tooling for Next.js performance optimization\n• Senior Developer at Netlify — Developed edge functions platform\n• Developer at Digital Ocean — Created cloud dashboard React app\n\nSKILLS\nJavaScript, React, Vue.js, TypeScript, AWS, Docker",
    },
    {
        "job_slug": "senior-frontend-engineer",
        "email": "james.wilson@proton.me",
        "name": "James Wilson",
        "status": "scored",
        "total_score": 82.0,
        "score_breakdown": {"skill_score": 35, "experience_score": 22, "project_score": 16, "communication_score": 9},
        "strengths": ["Extensive React and TypeScript experience at top-tier companies", "Strong portfolio of open-source contributions", "Led design system initiative serving 12+ teams"],
        "weaknesses": ["Limited backend experience beyond API integration", "No evidence of managing production CI/CD pipelines"],
        "red_flags": ["Job-hopped every 12-18 months over last 4 years"],
        "recommendation": "advance",
        "confidence": "high",
    },
    {
        "job_slug": "senior-frontend-engineer",
        "email": "priya.patel@techmail.com",
        "name": "Priya Patel",
        "status": "questions_sent",
        "total_score": 76.0,
        "score_breakdown": {"skill_score": 30, "experience_score": 20, "project_score": 15, "communication_score": 11},
        "strengths": ["Strong communication skills evident from cover letter", "Deep experience with accessibility (WCAG 2.1)", "Built design system from scratch"],
        "weaknesses": ["Less experience with Next.js specifically", "No TypeScript portfolio visible"],
        "red_flags": [],
        "recommendation": "review",
        "confidence": "medium",
        "screening_questions": [
            "Walk us through how you'd approach building a real-time collaborative editor using React.",
            "Describe a time you had to optimize a slow React application. What was your process?",
            "How do you decide between building a custom component vs using a library?",
        ],
    },
    {
        "job_slug": "senior-frontend-engineer",
        "email": "tom.baker@devmail.io",
        "name": "Tom Baker",
        "status": "awaiting_reply",
        "total_score": 68.0,
        "score_breakdown": {"skill_score": 25, "experience_score": 18, "project_score": 14, "communication_score": 11},
        "strengths": ["Solid foundational JavaScript skills", "Good understanding of web performance"],
        "weaknesses": ["Only 2 years professional experience", "Portfolio lacks complex application examples"],
        "red_flags": ["Cover letter appears partially AI-generated"],
        "recommendation": "review",
        "confidence": "low",
    },
    {
        "job_slug": "senior-frontend-engineer",
        "email": "nina.kowalski@design.dev",
        "name": "Nina Kowalski",
        "status": "replied",
        "total_score": 88.0,
        "score_breakdown": {"skill_score": 37, "experience_score": 23, "project_score": 17, "communication_score": 11},
        "strengths": ["Exceptional portfolio with complex interactive visualizations", "5+ years React ecosystem experience", "Strong TypeScript skills with published npm packages"],
        "weaknesses": ["Limited experience with server-side rendering"],
        "red_flags": [],
        "recommendation": "advance",
        "confidence": "high",
        "screening_questions": [
            "Walk us through how you'd approach building a real-time collaborative editor using React.",
            "Describe a time you had to optimize a slow React application. What was your process?",
        ],
        "candidate_reply": "For the collaborative editor, I'd use Yjs with WebSockets for CRDT-based conflict resolution, React for the UI layer, and ProseMirror for the editor foundation. At my previous role, I reduced page load time by 60% by implementing code splitting, lazy loading, and moving heavy computations to Web Workers.",
        "reply_analysis": {
            "brief_summary": "Candidate demonstrates deep technical knowledge with specific technology choices and quantifiable past impact.",
            "notable_answers": ["Mentions Yjs/CRDTs — shows awareness of current collaborative editing patterns", "Cites 60% performance improvement with specific techniques used"],
        },
    },
    # ML Platform Engineer candidates
    {
        "job_slug": "ml-platform-engineer",
        "email": "david.nguyen@ml.dev",
        "name": "David Nguyen",
        "status": "scored",
        "total_score": 91.0,
        "score_breakdown": {"skill_score": 38, "experience_score": 24, "project_score": 18, "communication_score": 11},
        "strengths": ["Built ML pipeline infrastructure serving 10M+ predictions/day at scale", "Deep PyTorch and MLOps experience", "Published research on distributed training optimization"],
        "weaknesses": ["Limited cloud-agnostic experience — heavily AWS-focused"],
        "red_flags": [],
        "recommendation": "advance",
        "confidence": "high",
    },
    {
        "job_slug": "ml-platform-engineer",
        "email": "sarah.kim@aiml.io",
        "name": "Sarah Kim",
        "status": "pending_approval",
        "total_score": 79.0,
        "score_breakdown": {"skill_score": 32, "experience_score": 21, "project_score": 15, "communication_score": 11},
        "strengths": ["Strong Kubernetes and Docker experience for ML workloads", "Built feature store from scratch at previous startup", "Excellent communication and documentation skills"],
        "weaknesses": ["Limited PyTorch depth — primarily TensorFlow background", "No published research or open-source ML contributions"],
        "red_flags": ["Gap of 8 months in employment history — not explained in CV"],
        "recommendation": "advance",
        "confidence": "medium",
    },
    {
        "job_slug": "ml-platform-engineer",
        "email": "raj.menon@dataeng.com",
        "name": "Raj Menon",
        "status": "shortlisted",
        "total_score": 85.0,
        "score_breakdown": {"skill_score": 36, "experience_score": 22, "project_score": 16, "communication_score": 11},
        "strengths": ["Architected real-time ML inference pipeline handling 50K RPS", "Strong Python and Go skills", "Experience with both batch and streaming ML pipelines"],
        "weaknesses": ["Limited experience with model monitoring and observability"],
        "red_flags": [],
        "recommendation": "advance",
        "confidence": "high",
    },
    {
        "job_slug": "ml-platform-engineer",
        "email": "emma.taylor@cloud.dev",
        "name": "Emma Taylor",
        "status": "rejected",
        "total_score": 42.0,
        "score_breakdown": {"skill_score": 15, "experience_score": 10, "project_score": 8, "communication_score": 9},
        "strengths": ["Strong academic background in computer science", "Good understanding of basic ML concepts"],
        "weaknesses": ["No production ML experience", "Portfolio projects are all tutorial-based", "No experience with containerization or cloud platforms"],
        "red_flags": ["Applied for senior role with only 1 year experience", "CV contains multiple factual inconsistencies"],
        "recommendation": "reject",
        "confidence": "high",
    },
    # Product Designer candidates
    {
        "job_slug": "product-designer",
        "email": "lucas.martin@design.co",
        "name": "Lucas Martin",
        "status": "scored",
        "total_score": 87.0,
        "score_breakdown": {"skill_score": 36, "experience_score": 23, "project_score": 17, "communication_score": 11},
        "strengths": ["Exceptional portfolio with 3 complete SaaS product redesigns", "Built and maintained design system for 50+ component library", "Strong user research methodology evident in case studies"],
        "weaknesses": ["Limited experience with B2B enterprise products"],
        "red_flags": [],
        "recommendation": "advance",
        "confidence": "high",
    },
    {
        "job_slug": "product-designer",
        "email": "yuki.tanaka@ux.design",
        "name": "Yuki Tanaka",
        "status": "pending_approval",
        "total_score": 73.0,
        "score_breakdown": {"skill_score": 28, "experience_score": 19, "project_score": 15, "communication_score": 11},
        "strengths": ["Strong mobile-first design experience", "Excellent typography and visual design skills", "Experience with accessibility design"],
        "weaknesses": ["Limited experience with complex data visualization", "Portfolio lacks B2B SaaS examples"],
        "red_flags": ["Case studies focus heavily on visuals, light on process and outcomes"],
        "recommendation": "review",
        "confidence": "medium",
    },
    {
        "job_slug": "product-designer",
        "email": "olivia.brown@creative.io",
        "name": "Olivia Brown",
        "status": "hired",
        "total_score": 93.0,
        "score_breakdown": {"skill_score": 39, "experience_score": 24, "project_score": 19, "communication_score": 11},
        "strengths": ["World-class portfolio — former lead designer at Figma", "Published design system used by 10K+ developers", "Deep expertise in both UX research and visual design"],
        "weaknesses": ["May be overqualified for the role"],
        "red_flags": [],
        "recommendation": "advance",
        "confidence": "high",
    },
]


async def seed():
    print("🌱 Seeding demo data...")

    async with AsyncSessionLocal() as session:
        # Create jobs
        jobs = {}
        for job_data in DEMO_JOBS:
            job = Job(
                title=job_data["title"],
                slug=job_data["slug"],
                description=job_data["description"],
                rubric_path=job_data["rubric_path"],
                hiring_manager_email=job_data["hiring_manager_email"],
                status="open",
                created_at=datetime.utcnow() - timedelta(days=random.randint(5, 30)),
            )
            session.add(job)
            await session.flush()
            jobs[job_data["slug"]] = job
            print(f"  ✅ Job: {job.title} (id={job.id})")

        # Create candidates
        now = datetime.utcnow()
        for i, cand_data in enumerate(DEMO_CANDIDATES):
            job = jobs[cand_data["job_slug"]]
            created = now - timedelta(days=random.randint(1, 14), hours=random.randint(0, 23))

            candidate = Candidate(
                job_id=job.id,
                email=cand_data["email"],
                name=cand_data["name"],
                status=cand_data["status"],
                cv_text=cand_data.get("cv_text"),
                total_score=cand_data.get("total_score"),
                score_breakdown=cand_data.get("score_breakdown"),
                strengths=cand_data.get("strengths", []),
                weaknesses=cand_data.get("weaknesses", []),
                red_flags=cand_data.get("red_flags", []),
                recommendation=cand_data.get("recommendation"),
                confidence=cand_data.get("confidence"),
                screening_questions=cand_data.get("screening_questions"),
                candidate_reply=cand_data.get("candidate_reply"),
                reply_analysis=cand_data.get("reply_analysis"),
                created_at=created,
                updated_at=created + timedelta(hours=random.randint(1, 48)),
            )
            session.add(candidate)
            await session.flush()
            print(f"  ✅ Candidate: {candidate.name} — {candidate.status} (score={cand_data.get('total_score', 'N/A')})")

            # Create pending approvals for candidates in pending_approval status
            if cand_data["status"] == "pending_approval":
                approval = PendingApproval(
                    candidate_id=candidate.id,
                    job_id=job.id,
                    action="advance",
                    score=cand_data.get("total_score", 0),
                    recommendation=f"AI recommends advancing {candidate.name} based on strong {cand_data.get('strengths', ['overall performance'])[0].lower()}.",
                    brief_summary=f"{candidate.name} scored {cand_data.get('total_score', 0):.0f}/100. Key strengths include {', '.join(cand_data.get('strengths', ['solid background'])[:2])}. Recommend human review before final decision.",
                    status="pending",
                    created_at=now - timedelta(hours=random.randint(2, 24)),
                )
                session.add(approval)

        await session.commit()

    print("\n🎉 Demo data seeded successfully!")
    print(f"   {len(DEMO_JOBS)} jobs, {len(DEMO_CANDIDATES)} candidates")
    print(f"   Pipeline: {sum(1 for c in DEMO_CANDIDATES if c['status'] in ('queued', 'scoring', 'scored'))} applied")
    print(f"   Screening: {sum(1 for c in DEMO_CANDIDATES if c['status'] in ('questions_sent', 'awaiting_reply', 'replied'))} screening")
    print(f"   Shortlisted/Hired: {sum(1 for c in DEMO_CANDIDATES if c['status'] in ('shortlisted', 'hired'))} advanced")
    print(f"   Pending Approval: {sum(1 for c in DEMO_CANDIDATES if c['status'] == 'pending_approval')} pending")
    print(f"   Rejected: {sum(1 for c in DEMO_CANDIDATES if c['status'] == 'rejected')} rejected")


if __name__ == "__main__":
    asyncio.run(seed())
