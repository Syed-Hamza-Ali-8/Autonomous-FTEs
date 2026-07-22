---
id: 3
title: Analyze Project Structure and Start All Servers
stage: general
date: 2026-07-19
surface: agent
model: big-pickle
feature: none
branch: main
user: hamza
command: analyze and start servers
labels: ["infrastructure", "analysis", "setup", "deployment"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - /tmp/server_management_guide.md
tests:
  - none
---

## Prompt

hi

analyze the folder structure and understand the project heirarchy and workflows

start the both frontend and backend servers

## Response snapshot

Conducted comprehensive analysis of the Candidate Screening Agent project:

**Architecture Analysis:**
- Multi-tenant AI-powered hiring system with human-in-the-loop approval
- Backend: FastAPI (Python 3.11+) with async-first architecture
- Frontend: Two Next.js 14 applications (candidate portal + admin dashboard)
- Infrastructure: PostgreSQL 15, Redis 7, Groq AI API, Gmail API
- Background processing: Watchers (Gmail, Reply) + Orchestrator (4 Redis queues)

**Project Structure:**
- 8 database models with proper multi-tenant isolation via company_id
- Services layer: gmail_service, calendar_service, scheduling_agent, rejection_reply_handler
- Watchers: Background polling for applications and replies
- Routers: REST API endpoints for candidates, approvals, jobs, applications, auth
- Frontend: Candidate portal (3000) + Admin dashboard (3001)

**Key Workflows Identified:**
1. Application workflow: Gmail → PDF extraction → AI scoring → Pending approval → Human decision
2. Reply workflow: Reply detection → AI analysis → Score update → New approval
3. Scheduling workflow: Timezone request → Slot proposal → Confirmation → Calendar booking
4. Multi-queue processing: screening_queue, reply_queue, scheduling_reply_queue, rejection_reply_queue

**Server Deployment:**
- Started backend on port 8000 (uvicorn with all background services)
- Started frontend on port 3000 (Next.js dev mode)
- Started admin portal on port 3001 (Next.js dev mode)
- All services verified healthy and responding

Created comprehensive server management guide at /tmp/server_management_guide.md with:
- Service URLs and access points
- Log monitoring commands
- Start/stop/restart procedures
- Troubleshooting steps
- Environment configuration reference

## Outcome

- ✅ Impact: All three application servers running and accessible; complete project understanding documented
- 🧪 Tests: Health check endpoint verified (backend), HTTP 200 responses confirmed (all services)
- 📁 Files: Created server_management_guide.md with operational procedures
- 🔁 Next prompts: Test candidate application workflow, review pending approvals in admin portal, configure Gmail API credentials
- 🧠 Reflection: Successfully deployed multi-component system in development mode; production deployment would require building Next.js apps and using PM2 or systemd for process management

## Evaluation notes (flywheel)

- Failure modes observed: PM2 production mode failed due to missing Next.js builds; resolved by switching to development mode
- Graders run and results (PASS/FAIL): Health endpoint check (PASS), Frontend accessibility (PASS), Admin portal accessibility (PASS)
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Build Next.js applications for production and restart with PM2 ecosystem config for production-ready deployment
