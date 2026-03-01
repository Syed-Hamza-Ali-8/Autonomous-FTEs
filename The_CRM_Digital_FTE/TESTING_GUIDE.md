# Testing Guide - Customer Success FTE

## Overview
This guide helps you test both the frontend (Next.js) and backend (FastAPI) while avoiding port conflicts with your Kiro service running on port 8001.

**Configuration:**
- Kiro Service: Port 8001 (already running - DO NOT STOP)
- Docker API: Port 8002 (configured to avoid conflict)
- Next.js Frontend: Port 3000
- PostgreSQL: Port 5432
- Kafka: Port 29092
- Kafka UI: Port 8080
- Grafana: Port 3000 (conflicts with Next.js - see note below)

---

## Prerequisites

1. **Docker and Docker Compose** installed
2. **Node.js 18+** and npm installed
3. **Kiro service running on port 8001** (leave it running)
4. **.env file** configured in project root

---

## Step 1: Start Docker Services (Backend Infrastructure)

### 1.1 Navigate to project directory
```bash
cd /mnt/d/hamza/autonomous-ftes/The_CRM_Digital_FTE
```

### 1.2 Check your .env file
Make sure you have a `.env` file with these variables:
```bash
# Database (Neon.tech or local)
DATABASE_URL=postgresql://fte_user:fte_password_change_me@localhost:5432/customer_success_fte

# OpenAI API Key (REQUIRED for AI responses)
OPENAI_API_KEY=your-openai-api-key-here

# Optional: OpenRouter (if using alternative to OpenAI)
# OPENAI_BASE_URL=https://openrouter.ai/api/v1
# OPENAI_MODEL=anthropic/claude-3.5-sonnet

# Twilio (Optional - for WhatsApp)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Grafana
GRAFANA_PASSWORD=admin_change_me

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 1.3 Start Docker services
```bash
# Start all services in detached mode
docker-compose up -d

# Check all services are running
docker-compose ps
```

**Expected output:**
```
NAME                    STATUS              PORTS
crm_fte_api            Up                  0.0.0.0:8002->8000/tcp
crm_fte_kafka          Up                  0.0.0.0:9092->9092/tcp, 0.0.0.0:29092->29092/tcp
crm_fte_postgres       Up (healthy)        0.0.0.0:5432->5432/tcp
crm_fte_redis          Up (healthy)        0.0.0.0:6379->6379/tcp
crm_fte_zookeeper      Up                  0.0.0.0:2181->2181/tcp
crm_fte_kafka_ui       Up                  0.0.0.0:8080->8080/tcp
crm_fte_prometheus     Up                  0.0.0.0:9090->9090/tcp
```

### 1.4 Check API health
```bash
# Test the API is responding on port 8002
curl http://localhost:8002/health

# Expected response:
# {"status":"healthy","database":"connected","kafka":"connected","timestamp":"..."}
```

### 1.5 View logs (if needed)
```bash
# View API logs
docker-compose logs -f api

# View worker logs
docker-compose logs -f worker

# View all logs
docker-compose logs -f
```

---

## Step 2: Start Frontend (Next.js)

### 2.1 Navigate to web directory
```bash
cd web
```

### 2.2 Install dependencies (first time only)
```bash
npm install
```

### 2.3 Verify .env.local configuration
The file `web/.env.local` should contain:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8002
```

### 2.4 Start Next.js development server
```bash
npm run dev
```

**Expected output:**
```
ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

**Note:** If port 3000 is already in use by Grafana, you can:
- Option A: Stop Grafana temporarily: `docker-compose stop grafana`
- Option B: Run Next.js on different port: `npm run dev -- -p 3001`

---

## Step 3: Test the System

### 3.1 Open the web form
Open your browser and navigate to:
```
http://localhost:3000/support
```

### 3.2 Submit a test ticket
Fill in the form:
- **Name:** Test User
- **Email:** test@example.com
- **Phone:** +1234567890 (optional)
- **Subject:** Testing the support system
- **Message:** This is a test message to verify the ticket creation system is working correctly.

Click **"Submit Support Request"**

### 3.3 Verify success
You should see:
- ✅ Green success message
- 📋 Ticket ID displayed (UUID format)
- Form resets

---

## Step 4: Verify Tickets in Database

### 4.1 Connect to PostgreSQL
```bash
# From project root directory
docker exec -it crm_fte_postgres psql -U fte_user -d customer_success_fte
```

### 4.2 Query tickets
```sql
-- View all tickets
SELECT id, subject, status, created_at
FROM tickets
ORDER BY created_at DESC
LIMIT 5;

-- View ticket details with customer info
SELECT
    t.id,
    t.subject,
    t.status,
    c.name as customer_name,
    c.email as customer_email,
    t.created_at
FROM tickets t
JOIN customers c ON t.customer_id = c.id
ORDER BY t.created_at DESC
LIMIT 5;

-- View messages for a specific ticket
SELECT
    m.role,
    m.content,
    m.channel,
    m.timestamp
FROM messages m
JOIN conversations conv ON m.conversation_id = conv.id
JOIN tickets t ON t.conversation_id = conv.id
WHERE t.id = 'YOUR-TICKET-ID-HERE'
ORDER BY m.timestamp;

-- Exit psql
\q
```

### 4.3 Alternative: Query via curl
```bash
# Get ticket by ID (replace with actual ticket ID)
curl http://localhost:8002/support/ticket/YOUR-TICKET-ID-HERE
```

---

## Step 5: Monitor System Activity

### 5.1 Kafka UI (View message flow)
Open browser:
```
http://localhost:8080
```
- Navigate to Topics → `fte.tickets.incoming`
- View messages being processed

### 5.2 Prometheus (View metrics)
Open browser:
```
http://localhost:9090
```
- Query: `fte_tickets_total`
- Query: `fte_processing_duration_seconds`

### 5.3 API Documentation
Open browser:
```
http://localhost:8002/docs
```
- Interactive API documentation (Swagger UI)
- Test endpoints directly

---

## Step 6: Test Different Scenarios

### 6.1 Test form validation
Try submitting with:
- Empty name → Should show error
- Invalid email → Should show error
- Message too short (<10 chars) → Should show error

### 6.2 Test multiple tickets
Submit 3-5 tickets with different subjects and verify:
```bash
# Count total tickets
docker exec -it crm_fte_postgres psql -U fte_user -d customer_success_fte -c "SELECT COUNT(*) FROM tickets;"
```

### 6.3 Test customer identification
Submit tickets with:
- Same email, different names → Should link to same customer
- Different emails → Should create different customers

Verify:
```sql
-- Connect to database
docker exec -it crm_fte_postgres psql -U fte_user -d customer_success_fte

-- Check customers
SELECT id, name, email, created_at FROM customers ORDER BY created_at DESC;

-- Check tickets per customer
SELECT
    c.email,
    COUNT(t.id) as ticket_count
FROM customers c
LEFT JOIN tickets t ON t.customer_id = c.id
GROUP BY c.email
ORDER BY ticket_count DESC;
```

---

## Troubleshooting

### Issue: Port 8002 already in use
```bash
# Find what's using port 8002
lsof -i :8002

# Or on Windows
netstat -ano | findstr :8002

# Stop the conflicting service or change docker-compose.yml to use another port
```

### Issue: Docker services won't start
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d

# Rebuild if needed
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Issue: Database connection failed
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Test connection
docker exec -it crm_fte_postgres psql -U fte_user -d customer_success_fte -c "SELECT 1;"
```

### Issue: Frontend can't connect to API
```bash
# Verify .env.local in web directory
cat web/.env.local

# Should show: NEXT_PUBLIC_API_URL=http://localhost:8002

# Test API directly
curl http://localhost:8002/health

# Check browser console for CORS errors
```

### Issue: Worker not processing messages
```bash
# Check worker logs
docker-compose logs worker

# Check Kafka is running
docker-compose ps kafka

# Verify OpenAI API key is set
docker-compose exec worker env | grep OPENAI_API_KEY
```

---

## Cleanup

### Stop all services (keep data)
```bash
cd /mnt/d/hamza/autonomous-ftes/The_CRM_Digital_FTE
docker-compose down
```

### Stop and remove all data
```bash
docker-compose down -v
```

### Stop only frontend
```bash
# In web directory, press Ctrl+C
```

---

## Quick Reference Commands

```bash
# Start everything
docker-compose up -d && cd web && npm run dev

# Check API health
curl http://localhost:8002/health

# View logs
docker-compose logs -f api worker

# Query database
docker exec -it crm_fte_postgres psql -U fte_user -d customer_success_fte

# Stop everything
docker-compose down && # Stop Next.js with Ctrl+C

# Restart API only
docker-compose restart api

# Restart worker only
docker-compose restart worker
```

---

## Success Criteria

✅ Docker services all show "Up" or "Up (healthy)"
✅ API responds at http://localhost:8002/health
✅ Frontend loads at http://localhost:3000/support
✅ Form submission shows success message with ticket ID
✅ Tickets appear in database
✅ Worker logs show message processing
✅ Kafka UI shows messages in topics

---

## Port Summary

| Service | Port | URL | Notes |
|---------|------|-----|-------|
| Kiro | 8001 | - | **DO NOT STOP** - Already running |
| Docker API | 8002 | http://localhost:8002 | Changed from 8001 |
| Next.js | 3000 | http://localhost:3000 | Frontend |
| PostgreSQL | 5432 | - | Database |
| Kafka | 29092 | - | Message broker |
| Kafka UI | 8080 | http://localhost:8080 | Kafka monitoring |
| Prometheus | 9090 | http://localhost:9090 | Metrics |
| Redis | 6379 | - | Cache |

---

**Generated:** 2026-02-28
**Project:** Customer Success Digital FTE
**Status:** Ready for Testing
