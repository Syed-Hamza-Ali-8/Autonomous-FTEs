# Quick Start Guide - Customer Success Digital FTE

Get the system running in **10 minutes** with this step-by-step guide.

---

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API account (required for AI responses)
- Gmail API credentials (optional - for email channel)
- Twilio account (optional - for WhatsApp channel)

---

## Step 1: Clone and Setup (2 minutes)

```bash
# Navigate to project directory
cd The_CRM_Digital_FTE

# Copy environment template
cp .env .env.backup  # Backup existing if needed

# The .env file already exists with placeholder values
```

---

## Step 2: Configure OpenAI API Key (2 minutes) ⚠️ **REQUIRED**

### Get Your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-...`)

### Update .env File

```bash
# Edit .env file
nano .env

# Find this line:
OPENAI_API_KEY=sk-your-openai-api-key-here

# Replace with your actual key:
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Save and exit (Ctrl+X, Y, Enter)
```

**⚠️ CRITICAL:** Without a valid OpenAI API key, the system will not create tickets or generate responses.

---

## Step 3: Start Infrastructure (3 minutes)

```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose ps

# You should see all services "Up" and "healthy"
```

**Expected Output:**
```
NAME                          STATUS
crm_fte_postgres              Up (healthy)
crm_fte_kafka                 Up (healthy)
crm_fte_redis                 Up (healthy)
crm_fte_zookeeper             Up
crm_fte_api                   Up (healthy)
the_crm_digital_fte-worker-1  Up
the_crm_digital_fte-worker-2  Up
```

---

## Step 4: Verify System Health (1 minute)

```bash
# Check API health
curl http://localhost:8001/health

# Expected output:
# {"status":"healthy","timestamp":"2026-02-22T...","version":"1.0.8"}

# Check database
docker exec -it crm_fte_postgres psql -U fte_user -d customer_success_fte -c "SELECT version();"

# Check Kafka topics
docker exec crm_fte_kafka kafka-topics --bootstrap-server localhost:9092 --list
```

---

## Step 5: Test Ticket Creation (2 minutes)

### Submit Test Ticket

```bash
curl -X POST http://localhost:8001/support/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "subject": "Testing the system",
    "message": "This is a test message to verify ticket creation and AI response generation."
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Your support request has been received. We'll respond shortly.",
  "ticket_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### Verify Ticket Was Created

```bash
# Wait 5 seconds for worker to process
sleep 5

# Check tickets table
docker exec -it crm_fte_postgres psql -U fte_user -d customer_success_fte \
  -c "SELECT id, subject, status, priority, created_at FROM tickets ORDER BY created_at DESC LIMIT 1;"
```

**Expected Output:**
```
                  id                  |      subject       | status | priority |         created_at
--------------------------------------+--------------------+--------+----------+----------------------------
 xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | Testing the system | open   | medium   | 2026-02-22 02:40:15.123456
```

### Check Worker Logs

```bash
# View worker processing logs
docker logs the_crm_digital_fte-worker-1 --tail 30

# Look for these success indicators:
# - "Processing message: ..."
# - "Agent response generated: ..."
# - "Ticket processed successfully in ...ms"
```

---

## Step 6: Access Web Form (1 minute)

### Start Next.js Development Server

```bash
# Navigate to web directory
cd web

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

### Test Web Form

1. Open browser to http://localhost:3000
2. Fill in the support form:
   - Name: Your Name
   - Email: your@email.com
   - Subject: Test from web form
   - Message: Testing the web form submission
3. Click "Submit Support Request"
4. You should see a success message with ticket ID

---

## Troubleshooting

### Issue: Tickets Not Being Created

**Symptom:** API returns success but no tickets in database

**Solution:**
```bash
# Check worker logs for errors
docker logs the_crm_digital_fte-worker-1 --tail 50

# Look for "401 Unauthorized" from OpenAI
# This means your API key is invalid

# Verify your API key is correct
cat .env | grep OPENAI_API_KEY

# If it shows placeholder, update with real key
nano .env

# Restart workers
docker-compose restart worker
```

### Issue: Services Not Starting

**Symptom:** `docker-compose ps` shows services as "Exited"

**Solution:**
```bash
# Check logs for specific service
docker-compose logs postgres
docker-compose logs kafka

# Restart all services
docker-compose down
docker-compose up -d

# Wait 60 seconds for Kafka to be ready
sleep 60
```

### Issue: Port Conflicts

**Symptom:** "Port already in use" error

**Solution:**
```bash
# Check what's using the port
lsof -i :8001  # API port
lsof -i :5432  # PostgreSQL port
lsof -i :9092  # Kafka port

# Either stop the conflicting service or change ports in docker-compose.yml
```

### Issue: Worker Not Processing Messages

**Symptom:** Messages in Kafka but no processing logs

**Solution:**
```bash
# Restart workers to trigger partition rebalancing
docker-compose restart worker

# Check consumer group status
docker exec crm_fte_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group fte-workers

# Look for "LAG" column - should be 0
```

---

## Optional: Add Gmail Integration (15 minutes)

### Prerequisites
- Google Cloud Project
- Gmail API enabled
- OAuth 2.0 credentials

### Steps

1. **Create Google Cloud Project**
   - Go to https://console.cloud.google.com
   - Create new project
   - Enable Gmail API

2. **Create OAuth Credentials**
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
   - Application type: Desktop app
   - Download credentials JSON

3. **Configure Application**
   ```bash
   # Create credentials directory
   mkdir -p credentials

   # Copy downloaded file
   cp ~/Downloads/client_secret_*.json credentials/gmail-credentials.json

   # Update .env
   nano .env
   # Set: GMAIL_CREDENTIALS_PATH=./credentials/gmail-credentials.json

   # Restart API
   docker-compose restart api
   ```

4. **Authenticate**
   ```bash
   # Run authentication flow (first time only)
   docker exec -it crm_fte_api python -c "from src.channels.gmail_integration import GmailIntegration; g = GmailIntegration(); g.authenticate()"

   # Follow the URL and authorize
   # Token will be saved to credentials/gmail-token.json
   ```

---

## Optional: Add WhatsApp Integration (10 minutes)

### Prerequisites
- Twilio account
- WhatsApp-enabled phone number

### Steps

1. **Get Twilio Credentials**
   - Go to https://console.twilio.com
   - Copy Account SID and Auth Token
   - Get WhatsApp-enabled number

2. **Configure Application**
   ```bash
   # Edit .env
   nano .env

   # Update these values:
   TWILIO_ACCOUNT_SID=your_actual_account_sid
   TWILIO_AUTH_TOKEN=your_actual_auth_token
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

   # Restart workers
   docker-compose restart worker
   ```

3. **Configure Webhook**
   - In Twilio Console, go to your WhatsApp number
   - Set webhook URL: `https://your-domain.com/webhooks/whatsapp`
   - Method: POST

---

## Next Steps

### Development
- Review API documentation: http://localhost:8001/docs
- Check metrics: http://localhost:8001/metrics
- View Grafana dashboards: http://localhost:3000 (admin/admin)
- Explore Kafka UI: http://localhost:8080

### Testing
```bash
# Run E2E tests
pytest tests/test_e2e_multichannel.py -v

# Run load tests
locust -f tests/load_test.py --host=http://localhost:8001
```

### Production Deployment
- See `DEPLOYMENT.md` for Kubernetes deployment
- See `RUNBOOK.md` for operational procedures
- See `COMPLETION_SUMMARY.md` for architecture overview

---

## System Architecture

```
┌─────────────┐
│  Web Form   │ ──┐
│ (Next.js)   │   │
└─────────────┘   │
                  │
┌─────────────┐   │    ┌──────────────┐    ┌─────────────┐
│   Gmail     │ ──┼───→│   FastAPI    │───→│   Kafka     │
│  (Email)    │   │    │     API      │    │   Topics    │
└─────────────┘   │    └──────────────┘    └─────────────┘
                  │                               │
┌─────────────┐   │                               ↓
│  WhatsApp   │ ──┘                        ┌─────────────┐
│  (Twilio)   │                            │   Workers   │
└─────────────┘                            │  (2 pods)   │
                                           └─────────────┘
                                                  │
                                                  ↓
                                           ┌─────────────┐
                                           │  OpenAI     │
                                           │   Agent     │
                                           └─────────────┘
                                                  │
                                                  ↓
                                           ┌─────────────┐
                                           │ PostgreSQL  │
                                           │  Database   │
                                           └─────────────┘
```

---

## Support

- **Documentation:** See `README.md`, `DEPLOYMENT.md`, `RUNBOOK.md`
- **Test Report:** See `TEST_REPORT.md` for comprehensive testing results
- **Investigation Report:** See `INVESTIGATION_REPORT.md` for debugging details
- **Completion Summary:** See `COMPLETION_SUMMARY.md` for hackathon status

---

## Cost Estimate

**Monthly Costs (10K messages/month):**
- OpenAI API (gpt-4o-mini): ~$65/month
- Twilio WhatsApp: ~$4/month
- Gmail API: Free
- Infrastructure (minimal): ~$12/month
- **Total: ~$81/month = $972/year** ✅ Under $1,000/year target

---

**Last Updated:** 2026-02-22
**System Status:** ✅ Production Ready (with valid credentials)
**Completion:** 95% - Architecture fully functional
