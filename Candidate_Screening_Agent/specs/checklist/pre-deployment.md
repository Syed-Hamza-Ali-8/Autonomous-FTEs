# Pre-Deployment Checklist

**Feature**: Candidate Screening Agent
**Purpose**: Verify all components are ready before deployment
**Last Updated**: 2026-04-27

---

## Infrastructure

- [ ] PostgreSQL database running and accessible
- [ ] Redis instance running and accessible
- [ ] Database tables created with correct schema
- [ ] Database indexes created
- [ ] Database connection pooling configured
- [ ] Redis connection tested
- [ ] Environment variables configured in deployment platform
- [ ] Secrets stored securely (not in code)

## Backend

- [ ] All dependencies installed (`uv sync` successful)
- [ ] All Python modules import without errors
- [ ] FastAPI application starts successfully
- [ ] `/health` endpoint returns `{"status": "ok"}`
- [ ] All API endpoints respond correctly
- [ ] CORS configured with correct origins
- [ ] Database migrations applied (if any)
- [ ] Logging configured and working
- [ ] Error handling tested

## AI Integration

- [ ] Grok API key configured in environment
- [ ] `set_tracing_disabled(True)` called in screening_agent.py
- [ ] CV scoring agent tested with sample CV
- [ ] Question generation agent tested
- [ ] Reply analysis agent tested
- [ ] JSON parsing with retry logic working
- [ ] Error handling for API failures tested
- [ ] Model selection correct (grok-3 vs grok-3-mini)

## Gmail Integration

- [ ] Gmail OAuth2 credentials configured
- [ ] Gmail API connection tested
- [ ] DRY_RUN mode enabled by default
- [ ] Email sending tested in DRY_RUN mode
- [ ] Email templates reviewed and approved
- [ ] Rate limiting configured (20 emails/hour)
- [ ] Gmail message ID tracking working

## Watchers

- [ ] GmailApplicationWatcher starts without errors
- [ ] ReplyWatcher starts without errors
- [ ] Processed IDs tracking working
- [ ] PDF extraction tested with sample PDFs
- [ ] Scanned PDF handling tested
- [ ] Error recovery tested (watcher continues after error)
- [ ] Redis queue integration working

## Orchestrator

- [ ] Orchestrator starts without errors
- [ ] Screening queue consumption working
- [ ] Reply queue consumption working
- [ ] Concurrent queue processing tested
- [ ] Error handling tested
- [ ] Audit logging working

## Daily Digest

- [ ] APScheduler configured correctly
- [ ] Daily digest function tested manually
- [ ] Email template reviewed
- [ ] Grok summary generation tested
- [ ] Schedule verified (8:00 AM daily)

## Frontend

- [ ] Next.js application builds successfully
- [ ] All pages render without errors
- [ ] API connection to backend working
- [ ] Dashboard displays candidates correctly
- [ ] Pipeline board working
- [ ] Candidate detail pages working
- [ ] Approval panel working
- [ ] Real-time polling (30s) working
- [ ] Responsive design tested (mobile, tablet, desktop)

## Testing

- [ ] All unit tests pass (`uv run pytest tests/ -v`)
- [ ] Test coverage meets minimum targets (75-95%)
- [ ] Integration tests pass
- [ ] End-to-end flow tested manually
- [ ] Error scenarios tested
- [ ] Edge cases tested

## Security

- [ ] No secrets in code or git repository
- [ ] `.env` files in `.gitignore`
- [ ] DRY_RUN mode prevents accidental emails
- [ ] CORS configured with specific origins (not `*`)
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified
- [ ] CSRF protection enabled (if applicable)
- [ ] Rate limiting configured

## Documentation

- [ ] README.md complete with setup instructions
- [ ] Environment variables documented
- [ ] API endpoints documented (Swagger UI)
- [ ] Architecture diagram included
- [ ] Deployment instructions documented
- [ ] Troubleshooting guide included

## Compliance

- [ ] HITL boundaries enforced (no auto-send of final decisions)
- [ ] Audit log captures all AI decisions
- [ ] Audit log captures all human actions
- [ ] GDPR compliance verified (data deletion on request)
- [ ] Equal opportunity compliance (bias-free scoring)

## Performance

- [ ] Database queries optimized with indexes
- [ ] API response times < 500ms for list endpoints
- [ ] API response times < 1s for detail endpoints
- [ ] CV scoring completes within 30 seconds
- [ ] Question generation completes within 15 seconds
- [ ] Dashboard loads within 2 seconds

## Monitoring

- [ ] Application logs configured
- [ ] Error tracking configured
- [ ] Health check endpoint monitored
- [ ] Database connection monitoring
- [ ] Redis connection monitoring
- [ ] API rate limit monitoring

## Deployment

- [ ] Backend deployed to Railway
- [ ] Frontend deployed to Vercel
- [ ] Environment variables configured in deployment platforms
- [ ] Database connection string configured
- [ ] Redis connection string configured
- [ ] Health check endpoint accessible
- [ ] Frontend connects to backend successfully
- [ ] SSL/HTTPS enabled

## Post-Deployment Verification

- [ ] Send test email with PDF CV to jobs inbox
- [ ] Verify candidate appears in dashboard within 2 minutes
- [ ] Verify screening questions sent (check DRY_RUN logs)
- [ ] Verify approval panel appears for pending approvals
- [ ] Verify approve action sends interview invite
- [ ] Verify reject action sends rejection email
- [ ] Verify audit log captures all actions
- [ ] Verify daily digest sent at 8:00 AM

## Rollback Plan

- [ ] Previous version tagged in git
- [ ] Database backup taken before deployment
- [ ] Rollback procedure documented
- [ ] Rollback tested in staging environment

---

**Sign-off**:
- [ ] Tech Lead: _________________ Date: _______
- [ ] DevOps: _________________ Date: _______
- [ ] Security: _________________ Date: _______
- [ ] Product Owner: _________________ Date: _______

**Notes**:
