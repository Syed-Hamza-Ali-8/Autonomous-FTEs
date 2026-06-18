# Security Checklist

**Feature**: Candidate Screening Agent
**Purpose**: Verify security measures before deployment
**Last Updated**: 2026-04-27

---

## Secrets Management

- [ ] No API keys hardcoded in source code
- [ ] No passwords hardcoded in source code
- [ ] No tokens hardcoded in source code
- [ ] All secrets stored in environment variables
- [ ] `.env` file in `.gitignore`
- [ ] `.env.example` provided with placeholder values
- [ ] No secrets in git history (check with `git log -p | grep -i "api_key"`)
- [ ] Secrets not exposed in logs
- [ ] Secrets not exposed in error messages
- [ ] Secrets not exposed in API responses
- [ ] OAuth2 refresh tokens stored securely
- [ ] Database credentials not in code

---

## Authentication & Authorization

### Gmail OAuth2

- [ ] OAuth2 flow implemented correctly
- [ ] Refresh token stored securely in environment
- [ ] Access token refreshed automatically before expiration
- [ ] Scopes limited to minimum required (`gmail.modify`, `gmail.send`)
- [ ] No credentials logged or exposed

### Grok API

- [ ] API key stored in environment variable
- [ ] API key not logged or exposed
- [ ] API requests use HTTPS only

### Future: Dashboard Authentication

- [ ] JWT-based authentication planned
- [ ] Password hashing with bcrypt/argon2
- [ ] Session management secure
- [ ] CSRF protection enabled

---

## Input Validation

### Email Addresses

- [ ] Email format validated (use Pydantic `EmailStr`)
- [ ] Email addresses sanitized before database storage
- [ ] Email addresses sanitized before sending emails

### File Uploads

- [ ] PDF file type validated (check MIME type)
- [ ] PDF file size limited (max 10MB)
- [ ] PDF content scanned for malware (future consideration)
- [ ] No arbitrary file execution

### API Inputs

- [ ] All request bodies validated with Pydantic models
- [ ] String lengths limited (prevent DoS)
- [ ] Numeric ranges validated (scores 0-100)
- [ ] Enum values validated (status, recommendation, confidence)
- [ ] SQL injection prevented (use ORM, no raw SQL)
- [ ] XSS prevented (escape HTML output)
- [ ] Command injection prevented (no shell execution with user input)

---

## Data Protection

### Candidate Data (PII)

- [ ] CV text stored encrypted at rest (future consideration)
- [ ] Email addresses not exposed in logs
- [ ] Names not exposed in logs
- [ ] Candidate data accessible only to authorized users
- [ ] GDPR compliance: data deletion on request
- [ ] Data retention policy documented (2 years)
- [ ] Audit log captures data access

### Audit Log

- [ ] Audit log immutable (no updates or deletes)
- [ ] Audit log captures all sensitive actions
- [ ] Audit log includes actor identity
- [ ] Audit log stored securely
- [ ] Audit log retention: 2 years minimum

### Database

- [ ] Database connection encrypted (SSL/TLS)
- [ ] Database credentials rotated regularly
- [ ] Database backups encrypted
- [ ] Database access restricted to application only
- [ ] No direct database access from public internet

---

## Network Security

### HTTPS/TLS

- [ ] All API endpoints use HTTPS in production
- [ ] TLS 1.2 or higher enforced
- [ ] Valid SSL certificate installed
- [ ] HTTP redirects to HTTPS
- [ ] HSTS header enabled

### CORS

- [ ] CORS configured with specific origins (not `*`)
- [ ] CORS allows only required methods
- [ ] CORS allows only required headers
- [ ] Preflight requests handled correctly

### Rate Limiting

- [ ] Gmail API rate limiting respected (20 emails/hour)
- [ ] API rate limiting planned (100 req/min per IP)
- [ ] DDoS protection considered (Cloudflare, AWS Shield)

---

## Application Security

### Dependency Security

- [ ] All dependencies up to date
- [ ] No known vulnerabilities in dependencies (run `pip-audit`)
- [ ] Dependency versions pinned in `pyproject.toml`
- [ ] Regular dependency updates scheduled

### Code Security

- [ ] No `eval()` or `exec()` usage
- [ ] No `pickle` usage (unsafe deserialization)
- [ ] No shell command execution with user input
- [ ] No file path traversal vulnerabilities
- [ ] Error messages don't expose sensitive information
- [ ] Stack traces not exposed to users in production

### Session Security

- [ ] Session tokens use secure random generation
- [ ] Session tokens expire after inactivity
- [ ] Session tokens invalidated on logout
- [ ] Session fixation prevented

---

## Infrastructure Security

### Docker

- [ ] Docker images from trusted sources only
- [ ] Docker images scanned for vulnerabilities
- [ ] Containers run as non-root user
- [ ] Secrets not baked into Docker images
- [ ] Docker Compose files don't expose unnecessary ports

### Cloud Deployment

- [ ] Railway environment variables encrypted
- [ ] Vercel environment variables encrypted
- [ ] Database not publicly accessible
- [ ] Redis not publicly accessible
- [ ] Firewall rules restrict access to necessary ports only
- [ ] SSH access restricted to authorized IPs

### Monitoring

- [ ] Failed login attempts monitored
- [ ] Unusual API activity monitored
- [ ] Database access monitored
- [ ] Error rates monitored
- [ ] Security alerts configured

---

## HITL Security

### Approval Process

- [ ] No auto-approval of candidates (HITL enforced)
- [ ] Approval actions require explicit user action
- [ ] Approver identity captured in audit log
- [ ] Approval expiration enforced (48 hours)
- [ ] Expired approvals cannot be processed

### Email Sending

- [ ] Interview invites sent only after approval
- [ ] Rejection emails sent only after approval
- [ ] DRY_RUN mode prevents accidental emails
- [ ] Email sending logged to audit log
- [ ] Email recipients validated before sending

---

## Compliance

### GDPR

- [ ] Data deletion on request implemented
- [ ] Data retention policy documented
- [ ] Privacy policy available
- [ ] Consent for data processing obtained
- [ ] Data processing agreement with third parties (Grok, Gmail)
- [ ] Data breach notification procedure documented

### Equal Opportunity

- [ ] AI scoring bias-free (regular audits)
- [ ] No demographic data collected (unless legally required)
- [ ] Scoring criteria objective and job-related
- [ ] Human review required for final decisions
- [ ] Audit log enables bias detection

### Data Retention

- [ ] Candidate data retained for 2 years
- [ ] Audit log retained for 2 years minimum
- [ ] Data deletion procedure documented
- [ ] Backup retention policy documented

---

## Incident Response

### Security Incident Plan

- [ ] Incident response plan documented
- [ ] Security contact designated
- [ ] Incident escalation procedure defined
- [ ] Data breach notification procedure defined
- [ ] Post-incident review process defined

### Backup & Recovery

- [ ] Database backups automated (daily)
- [ ] Backup encryption enabled
- [ ] Backup restoration tested
- [ ] Disaster recovery plan documented
- [ ] RTO (Recovery Time Objective) defined: 4 hours
- [ ] RPO (Recovery Point Objective) defined: 24 hours

---

## Penetration Testing

### Manual Testing

- [ ] SQL injection attempts tested
- [ ] XSS attempts tested
- [ ] CSRF attempts tested
- [ ] Authentication bypass attempts tested
- [ ] Authorization bypass attempts tested
- [ ] File upload vulnerabilities tested
- [ ] API abuse tested

### Automated Scanning

- [ ] OWASP ZAP scan completed
- [ ] Dependency vulnerability scan completed (`pip-audit`)
- [ ] Docker image vulnerability scan completed
- [ ] No critical vulnerabilities found

---

## Security Headers

### HTTP Headers

- [ ] `Strict-Transport-Security` (HSTS) enabled
- [ ] `X-Content-Type-Options: nosniff` enabled
- [ ] `X-Frame-Options: DENY` enabled
- [ ] `X-XSS-Protection: 1; mode=block` enabled
- [ ] `Content-Security-Policy` configured
- [ ] `Referrer-Policy: no-referrer` enabled

### CORS Headers

- [ ] `Access-Control-Allow-Origin` set to specific origins
- [ ] `Access-Control-Allow-Methods` limited to required methods
- [ ] `Access-Control-Allow-Headers` limited to required headers
- [ ] `Access-Control-Allow-Credentials` set appropriately

---

## Logging & Monitoring

### Security Logging

- [ ] All authentication attempts logged
- [ ] All authorization failures logged
- [ ] All data access logged
- [ ] All configuration changes logged
- [ ] Logs stored securely
- [ ] Logs not containing sensitive data (PII, secrets)

### Monitoring

- [ ] Failed authentication attempts monitored
- [ ] Unusual API activity monitored
- [ ] Database access patterns monitored
- [ ] Error rates monitored
- [ ] Security alerts configured (email, Slack)

---

## Third-Party Security

### Grok API (xAI)

- [ ] Data processing agreement reviewed
- [ ] Privacy policy reviewed
- [ ] Data residency requirements met
- [ ] API key rotation procedure defined
- [ ] Service availability SLA reviewed

### Gmail API (Google)

- [ ] OAuth2 scopes minimized
- [ ] Data processing agreement reviewed
- [ ] Privacy policy reviewed
- [ ] API quota limits understood
- [ ] Service availability SLA reviewed

### Railway (Backend Hosting)

- [ ] Security features enabled
- [ ] Environment variables encrypted
- [ ] Access control configured
- [ ] Audit logging enabled

### Vercel (Frontend Hosting)

- [ ] Security features enabled
- [ ] Environment variables encrypted
- [ ] Access control configured
- [ ] Audit logging enabled

---

## Security Training

### Development Team

- [ ] OWASP Top 10 training completed
- [ ] Secure coding practices training completed
- [ ] GDPR compliance training completed
- [ ] Incident response training completed

### Operations Team

- [ ] Security monitoring training completed
- [ ] Incident response training completed
- [ ] Backup/recovery training completed

---

## Security Checklist Sign-off

- [ ] Security Lead: _________________ Date: _______
- [ ] Tech Lead: _________________ Date: _______
- [ ] Compliance Officer: _________________ Date: _______
- [ ] Legal Review: _________________ Date: _______

**Critical Issues Found**: _______

**Remediation Plan**: _______

**Approved for Production**: ☐ Yes ☐ No

**Notes**:
