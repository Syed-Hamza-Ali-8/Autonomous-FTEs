# Security Guide - Customer Success Digital FTE

## Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [API Security](#api-security)
4. [Webhook Security](#webhook-security)
5. [Secret Management](#secret-management)
6. [Network Security](#network-security)
7. [Data Protection](#data-protection)
8. [Monitoring & Auditing](#monitoring--auditing)
9. [Compliance](#compliance)

---

## Security Overview

### Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Least Privilege**: Minimal permissions required
3. **Zero Trust**: Verify everything, trust nothing
4. **Encryption Everywhere**: Data encrypted in transit and at rest
5. **Audit Everything**: Comprehensive logging and monitoring

### Threat Model

**Assets:**
- Customer data (PII: names, emails, phone numbers)
- Conversation history
- API keys (OpenAI, Twilio, Gmail)
- Database credentials

**Threats:**
- Unauthorized access to customer data
- API key theft
- Webhook spoofing
- SQL injection
- XSS attacks
- DDoS attacks
- Man-in-the-middle attacks

**Mitigations:**
- TLS encryption for all traffic
- API authentication
- Webhook signature verification
- Input validation and sanitization
- Rate limiting
- Network policies
- Secret encryption

---

## Authentication & Authorization

### API Authentication

**Implementation: API Key Authentication**

```python
# src/api/auth.py
"""
API Authentication Middleware
"""

import os
import secrets
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Valid API keys (in production, store in database)
VALID_API_KEYS = set(os.getenv("API_KEYS", "").split(","))


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key from request header.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        API key if valid

    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key"
        )

    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return api_key


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)
```

**Usage in Endpoints:**

```python
from fastapi import Depends
from .auth import verify_api_key

@app.get("/customers/lookup")
async def lookup_customer(
    email: str,
    api_key: str = Depends(verify_api_key)
):
    # Only accessible with valid API key
    ...
```

### Role-Based Access Control (RBAC)

**Kubernetes RBAC Configuration:**

```yaml
# k8s/rbac.yaml
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: fte-api-sa
  namespace: customer-success-fte

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: fte-api-role
  namespace: customer-success-fte
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: fte-api-rolebinding
  namespace: customer-success-fte
subjects:
- kind: ServiceAccount
  name: fte-api-sa
  namespace: customer-success-fte
roleRef:
  kind: Role
  name: fte-api-role
  apiGroup: rbac.authorization.k8s.io
```

---

## API Security

### Rate Limiting

**Implementation using slowapi:**

```python
# src/api/rate_limit.py
"""
Rate Limiting Middleware
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)

# Add to FastAPI app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Usage in endpoints
@app.post("/support/submit")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def submit_support_request(request: Request, submission: WebFormSubmission):
    ...
```

**Rate Limit Configuration:**

- Web form submissions: 10/minute per IP
- WhatsApp webhooks: 100/minute per phone number
- Gmail webhooks: 50/minute
- Customer lookup: 30/minute per API key

### Input Validation

**Pydantic Models with Validation:**

```python
from pydantic import BaseModel, EmailStr, Field, validator
import re

class WebFormSubmission(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    subject: str = Field(..., min_length=1, max_length=500)
    message: str = Field(..., min_length=10, max_length=5000)

    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^\+?[1-9]\d{1,14}$', v):
            raise ValueError('Invalid phone number format')
        return v

    @validator('message')
    def sanitize_message(cls, v):
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&']
        for char in dangerous_chars:
            v = v.replace(char, '')
        return v
```

### Security Headers

**Implementation:**

```python
# src/api/security_headers.py
"""
Security Headers Middleware
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response

# Add to FastAPI app
app.add_middleware(SecurityHeadersMiddleware)
```

### CORS Configuration

**Secure CORS Setup:**

```python
from fastapi.middleware.cors import CORSMiddleware

# Restrict CORS to specific origins
allowed_origins = [
    "https://support.techcorp.com",
    "https://www.techcorp.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Don't use "*" in production
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only needed methods
    allow_headers=["Content-Type", "X-API-Key"],
    max_age=3600
)
```

---

## Webhook Security

### WhatsApp Webhook Verification

**Already Implemented:**

```python
# src/channels/whatsapp_integration.py
def validate_webhook(self, url: str, params: Dict[str, Any], signature: str) -> bool:
    """Validate Twilio webhook signature."""
    return self.validator.validate(url, params, signature)
```

**Usage in Endpoint:**

```python
@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(
    request: Request,
    x_twilio_signature: Optional[str] = Header(None)
):
    # Get form data
    form_data = await request.form()
    webhook_data = dict(form_data)

    # Validate signature
    if x_twilio_signature:
        url = str(request.url)
        is_valid = whatsapp.validate_webhook(url, webhook_data, x_twilio_signature)
        if not is_valid:
            raise HTTPException(status_code=403, detail="Invalid signature")

    # Process webhook
    ...
```

### Gmail Webhook Verification

**Implementation:**

```python
# src/channels/gmail_integration.py
import base64
import json
from google.oauth2 import service_account
from google.auth.transport import requests

def verify_pubsub_token(token: str) -> bool:
    """
    Verify Google Pub/Sub JWT token.

    Args:
        token: JWT token from Pub/Sub

    Returns:
        True if valid
    """
    try:
        # Verify JWT signature
        request = requests.Request()
        id_info = id_token.verify_oauth2_token(token, request)

        # Verify issuer
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return False

        return True
    except Exception:
        return False
```

---

## Secret Management

### Kubernetes Secrets

**Create Secrets:**

```bash
# Create secrets from files
kubectl create secret generic fte-secrets \
  --from-literal=DATABASE_PASSWORD='your-db-password' \
  --from-literal=OPENAI_API_KEY='sk-your-key' \
  --from-literal=TWILIO_ACCOUNT_SID='ACxxxx' \
  --from-literal=TWILIO_AUTH_TOKEN='your-token' \
  --from-file=GMAIL_CREDENTIALS=credentials.json \
  -n customer-success-fte

# Verify secrets
kubectl get secrets -n customer-success-fte
```

**Encrypt Secrets at Rest:**

```yaml
# Enable encryption at rest in Kubernetes
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64-encoded-32-byte-key>
      - identity: {}
```

### External Secret Management

**Using AWS Secrets Manager:**

```yaml
# k8s/external-secrets.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: customer-success-fte
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: fte-api-sa

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: fte-secrets
  namespace: customer-success-fte
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: fte-secrets
  data:
    - secretKey: OPENAI_API_KEY
      remoteRef:
        key: fte/openai-api-key
    - secretKey: DATABASE_PASSWORD
      remoteRef:
        key: fte/database-password
```

### Secret Rotation

**Automated Secret Rotation:**

```bash
#!/bin/bash
# scripts/rotate-secrets.sh

# Rotate OpenAI API key
NEW_KEY=$(generate_new_openai_key)
kubectl patch secret fte-secrets -n customer-success-fte \
  -p "{\"data\":{\"OPENAI_API_KEY\":\"$(echo -n $NEW_KEY | base64)\"}}"

# Restart pods to pick up new secret
kubectl rollout restart deployment/fte-api -n customer-success-fte
kubectl rollout restart deployment/fte-worker -n customer-success-fte

# Verify rollout
kubectl rollout status deployment/fte-api -n customer-success-fte
```

---

## Network Security

### Network Policies

**Restrict Pod-to-Pod Communication:**

```yaml
# k8s/network-policies.yaml
---
# Default deny all ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: customer-success-fte
spec:
  podSelector: {}
  policyTypes:
  - Ingress

---
# Allow API to access database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-to-postgres
  namespace: customer-success-fte
spec:
  podSelector:
    matchLabels:
      app: postgres
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: fte-api
    - podSelector:
        matchLabels:
          app: fte-worker
    ports:
    - protocol: TCP
      port: 5432

---
# Allow API to access Kafka
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-to-kafka
  namespace: customer-success-fte
spec:
  podSelector:
    matchLabels:
      app: kafka
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: fte-api
    - podSelector:
        matchLabels:
          app: fte-worker
    ports:
    - protocol: TCP
      port: 9092

---
# Allow external traffic to API
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-ingress
  namespace: customer-success-fte
spec:
  podSelector:
    matchLabels:
      app: fte-api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 8000
```

### TLS/SSL Configuration

**Ingress with TLS:**

```yaml
# k8s/ingress-tls.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fte-ingress-tls
  namespace: customer-success-fte
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - support.techcorp.com
    secretName: fte-tls-cert
  rules:
  - host: support.techcorp.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fte-api-service
            port:
              number: 80
```

**Certificate Management with cert-manager:**

```yaml
# k8s/cert-manager.yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@techcorp.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

---

## Data Protection

### Encryption at Rest

**PostgreSQL Encryption:**

```sql
-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt sensitive fields
CREATE TABLE customers (
    id UUID PRIMARY KEY,
    email VARCHAR(255),
    phone VARCHAR(50),
    name VARCHAR(255),
    encrypted_notes TEXT,  -- Encrypted field
    encryption_key_id VARCHAR(50)
);

-- Encrypt data
INSERT INTO customers (id, email, encrypted_notes, encryption_key_id)
VALUES (
    uuid_generate_v4(),
    'customer@example.com',
    pgp_sym_encrypt('Sensitive notes', 'encryption-key'),
    'key-v1'
);

-- Decrypt data
SELECT
    email,
    pgp_sym_decrypt(encrypted_notes::bytea, 'encryption-key') as notes
FROM customers;
```

### Data Retention

**Automated Data Cleanup:**

```sql
-- Delete old conversations (90 days)
DELETE FROM conversations
WHERE status = 'closed'
AND updated_at < NOW() - INTERVAL '90 days';

-- Archive old messages
INSERT INTO messages_archive
SELECT * FROM messages
WHERE created_at < NOW() - INTERVAL '180 days';

DELETE FROM messages
WHERE created_at < NOW() - INTERVAL '180 days';
```

### PII Handling

**Data Minimization:**
- Only collect necessary PII
- Anonymize data where possible
- Implement right to deletion (GDPR)

**PII Deletion Script:**

```python
# scripts/delete_customer_data.py
async def delete_customer_data(customer_id: UUID):
    """Delete all customer data (GDPR right to deletion)."""
    async with get_db_context() as db:
        # Delete messages
        await db.execute(
            delete(Message).where(
                Message.conversation_id.in_(
                    select(Conversation.id).where(
                        Conversation.customer_id == customer_id
                    )
                )
            )
        )

        # Delete conversations
        await db.execute(
            delete(Conversation).where(Conversation.customer_id == customer_id)
        )

        # Delete tickets
        await db.execute(
            delete(Ticket).where(Ticket.customer_id == customer_id)
        )

        # Delete customer identifiers
        await db.execute(
            delete(CustomerIdentifier).where(
                CustomerIdentifier.customer_id == customer_id
            )
        )

        # Delete customer
        await db.execute(
            delete(Customer).where(Customer.id == customer_id)
        )

        await db.commit()
```

---

## Monitoring & Auditing

### Audit Logging

**Implementation:**

```python
# src/monitoring/audit_log.py
import logging
from datetime import datetime
from typing import Dict, Any

audit_logger = logging.getLogger("audit")

def log_audit_event(
    event_type: str,
    user_id: str,
    resource_type: str,
    resource_id: str,
    action: str,
    result: str,
    metadata: Dict[str, Any] = None
):
    """Log audit event."""
    audit_logger.info(
        "AUDIT",
        extra={
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "result": result,
            "metadata": metadata or {}
        }
    )

# Usage
log_audit_event(
    event_type="customer_lookup",
    user_id="api-key-123",
    resource_type="customer",
    resource_id=str(customer_id),
    action="read",
    result="success"
)
```

### Security Monitoring

**Alert on Suspicious Activity:**

```yaml
# Prometheus alert rules
groups:
- name: security_alerts
  rules:
  - alert: HighFailedAuthRate
    expr: rate(fte_http_requests_total{status="401"}[5m]) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High rate of failed authentication attempts"

  - alert: UnusualTrafficPattern
    expr: rate(fte_http_requests_total[5m]) > 100
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Unusual traffic pattern detected"
```

---

## Compliance

### GDPR Compliance

**Requirements:**
- Right to access: Customer can request their data
- Right to deletion: Customer can request data deletion
- Right to portability: Customer can export their data
- Data breach notification: Within 72 hours

**Implementation:**

```python
# Export customer data (GDPR right to portability)
async def export_customer_data(customer_id: UUID) -> Dict[str, Any]:
    """Export all customer data."""
    async with get_db_context() as db:
        # Get customer
        customer = await db.get(Customer, customer_id)

        # Get conversations
        conversations = await db.execute(
            select(Conversation).where(Conversation.customer_id == customer_id)
        )

        # Get messages
        messages = await db.execute(
            select(Message).where(
                Message.conversation_id.in_([c.id for c in conversations])
            )
        )

        return {
            "customer": customer.to_dict(),
            "conversations": [c.to_dict() for c in conversations],
            "messages": [m.to_dict() for m in messages]
        }
```

### SOC 2 Compliance

**Controls:**
- Access control (RBAC)
- Encryption (TLS, at-rest)
- Monitoring and logging
- Incident response procedures
- Change management
- Vendor management

---

## Security Checklist

### Pre-Production

- [ ] All secrets stored securely (not in code)
- [ ] TLS enabled for all endpoints
- [ ] API authentication implemented
- [ ] Rate limiting configured
- [ ] Webhook signature verification enabled
- [ ] Input validation on all endpoints
- [ ] Security headers configured
- [ ] CORS properly restricted
- [ ] Network policies applied
- [ ] RBAC configured
- [ ] Audit logging enabled
- [ ] Security monitoring alerts configured

### Post-Production

- [ ] Regular security audits
- [ ] Penetration testing
- [ ] Dependency vulnerability scanning
- [ ] Secret rotation procedures
- [ ] Incident response plan tested
- [ ] Backup and recovery tested
- [ ] Compliance requirements met

---

## Security Contacts

- Security Team: security@techcorp.com
- Incident Response: incidents@techcorp.com
- Bug Bounty: https://techcorp.com/security/bug-bounty
