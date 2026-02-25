# OpenRouter Setup Guide - FREE Alternative to OpenAI

This guide shows you how to use **OpenRouter** instead of OpenAI, which offers:
- ✅ **FREE tier available** (no credit card required)
- ✅ **No embeddings required** (works with free accounts)
- ✅ **Multiple model options** (including free models)
- ✅ **Compatible with OpenAI SDK** (drop-in replacement)

---

## Why OpenRouter?

**Problem:** OpenAI requires a paid account for embeddings API access.

**Solution:** OpenRouter provides free access to various AI models without requiring embeddings.

**What You Get:**
- Free models: Llama 3.1, Mistral, Gemini Flash, and more
- Paid models: GPT-4, Claude, and others (if you add credits)
- No embeddings needed (system uses text search instead)

---

## Step 1: Get Your OpenRouter API Key (2 minutes)

### Create Account
1. Go to https://openrouter.ai/
2. Click "Sign In" (top right)
3. Sign in with Google, GitHub, or email
4. No credit card required for free tier!

### Get API Key
1. After signing in, go to https://openrouter.ai/keys
2. Click "Create Key"
3. Give it a name (e.g., "Customer Success FTE")
4. Copy the key (starts with `sk-or-v1-...`)

**Important:** Save this key somewhere safe - you won't be able to see it again!

---

## Step 2: Configure Your Application (1 minute)

### Edit .env File

```bash
# Open .env file
nano .env
```

### Update These Lines

```bash
# ============================================================================
# OPENAI API (or OpenRouter)
# ============================================================================
# Replace with your actual OpenRouter API key
OPENAI_API_KEY=sk-or-v1-your-actual-openrouter-key-here
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# Choose a model (see options below)
OPENAI_MODEL=meta-llama/llama-3.1-8b-instruct:free

# Disable embeddings (not needed with OpenRouter)
ENABLE_EMBEDDINGS=false
```

**Save and exit:** Ctrl+X, Y, Enter

---

## Step 3: Choose Your Model

OpenRouter offers many models. Here are the best options:

### FREE Models (No Cost)

```bash
# Llama 3.1 8B - Fast, good quality, completely free
OPENAI_MODEL=meta-llama/llama-3.1-8b-instruct:free

# Mistral 7B - Fast, good for customer support
OPENAI_MODEL=mistralai/mistral-7b-instruct:free

# Google Gemini Flash - Very fast, good quality
OPENAI_MODEL=google/gemini-flash-1.5:free

# Qwen 2.5 7B - Good multilingual support
OPENAI_MODEL=qwen/qwen-2.5-7b-instruct:free
```

### Paid Models (If You Add Credits)

```bash
# GPT-4o Mini - Best value, $0.15/1M tokens
OPENAI_MODEL=openai/gpt-4o-mini

# Claude 3.5 Sonnet - Excellent quality, $3/1M tokens
OPENAI_MODEL=anthropic/claude-3.5-sonnet

# GPT-4 Turbo - Most capable, $10/1M tokens
OPENAI_MODEL=openai/gpt-4-turbo
```

**Recommendation:** Start with `meta-llama/llama-3.1-8b-instruct:free` - it's completely free and works well for customer support.

---

## Step 4: Start the System (3 minutes)

```bash
# Restart all services to pick up new configuration
docker-compose down
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose ps

# Check worker logs to verify OpenRouter connection
docker logs the_crm_digital_fte-worker-1 --tail 20
```

**Expected Output:**
```
2026-02-22 03:00:00 - INFO - Kafka worker ready to process messages
2026-02-22 03:00:00 - INFO - Starting message processing loop...
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
    "subject": "Testing OpenRouter integration",
    "message": "This is a test to verify that OpenRouter is working correctly with the customer success agent."
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
# Wait 5-10 seconds for processing (free models may be slower)
sleep 10

# Check tickets table
docker exec -it crm_fte_postgres psql -U fte_user -d customer_success_fte \
  -c "SELECT id, subject, status, priority FROM tickets ORDER BY created_at DESC LIMIT 1;"
```

**Expected Output:**
```
                  id                  |            subject             | status | priority
--------------------------------------+--------------------------------+--------+----------
 xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | Testing OpenRouter integration | open   | medium
```

### Check Worker Logs for Success

```bash
docker logs the_crm_digital_fte-worker-1 --tail 50 | grep -A 5 "Processing message"
```

**Look for:**
```
INFO - Processing message: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
INFO - Agent response generated: 150 chars
INFO - Ticket processed successfully in 2500.00ms
```

---

## Troubleshooting

### Issue: 401 Unauthorized

**Symptom:** Worker logs show "HTTP/1.1 401 Unauthorized"

**Cause:** Invalid OpenRouter API key

**Solution:**
```bash
# Verify your API key is correct
cat .env | grep OPENAI_API_KEY

# Should show: OPENAI_API_KEY=sk-or-v1-...
# If it shows placeholder, update with real key

# Get new key from https://openrouter.ai/keys
nano .env

# Restart workers
docker-compose restart worker
```

### Issue: Model Not Found

**Symptom:** Error: "Model not found" or "Invalid model"

**Cause:** Model name incorrect or not available

**Solution:**
```bash
# Check available models at https://openrouter.ai/models

# Update .env with correct model name
nano .env

# Common mistake: Missing ":free" suffix for free models
# Correct: meta-llama/llama-3.1-8b-instruct:free
# Wrong: meta-llama/llama-3.1-8b-instruct

# Restart workers
docker-compose restart worker
```

### Issue: Slow Response Times

**Symptom:** Tickets take 10-30 seconds to process

**Cause:** Free models may have rate limits or queuing

**Solutions:**
1. **Use faster free model:**
   ```bash
   OPENAI_MODEL=google/gemini-flash-1.5:free
   ```

2. **Add credits and use paid model:**
   - Go to https://openrouter.ai/credits
   - Add $5-10 credits
   - Use: `openai/gpt-4o-mini` (fast and cheap)

3. **Accept slower processing:**
   - Free models work fine, just slower
   - Still much cheaper than human support!

### Issue: Rate Limits

**Symptom:** "Rate limit exceeded" errors

**Cause:** Free tier has usage limits

**Solutions:**
1. **Wait a few minutes** - limits reset quickly
2. **Add credits** - removes most rate limits
3. **Use different free model** - each has separate limits

---

## Cost Comparison

### FREE Tier (OpenRouter)
- **Cost:** $0/month
- **Models:** Llama 3.1, Mistral, Gemini Flash
- **Limits:** ~200 requests/day per model
- **Best for:** Testing, low-volume support

### Paid Tier (OpenRouter with Credits)
- **Cost:** ~$5-20/month (pay as you go)
- **Models:** GPT-4o Mini, Claude, GPT-4
- **Limits:** Very high (based on credits)
- **Best for:** Production use

### Comparison to OpenAI Direct
| Feature | OpenRouter Free | OpenRouter Paid | OpenAI Direct |
|---------|----------------|-----------------|---------------|
| Monthly Cost | $0 | $5-20 | $20-50 |
| Embeddings | Not needed | Optional | Required ($) |
| Free Tier | ✅ Yes | N/A | ❌ No |
| Model Choice | 10+ free models | 50+ models | OpenAI only |
| Setup | Easy | Easy | Complex |

---

## Advanced Configuration

### Using Multiple Models

You can configure different models for different purposes:

```bash
# .env configuration
OPENAI_MODEL=meta-llama/llama-3.1-8b-instruct:free  # Main model
OPENAI_FALLBACK_MODEL=google/gemini-flash-1.5:free  # Backup if rate limited
```

### Monitoring Usage

Check your OpenRouter usage:
1. Go to https://openrouter.ai/activity
2. View requests, costs, and rate limits
3. See which models you're using most

### Adding Credits (Optional)

If you want faster/better models:
1. Go to https://openrouter.ai/credits
2. Add $5-10 to start
3. Credits never expire
4. Pay only for what you use

**Recommended:** Start free, add credits only if needed

---

## Model Recommendations by Use Case

### Best for Customer Support (Free)
```bash
OPENAI_MODEL=meta-llama/llama-3.1-8b-instruct:free
```
- Good quality responses
- Understands context well
- Completely free
- Reasonable speed

### Best for Speed (Free)
```bash
OPENAI_MODEL=google/gemini-flash-1.5:free
```
- Very fast responses
- Good quality
- Free tier
- Google's latest model

### Best for Quality (Paid)
```bash
OPENAI_MODEL=anthropic/claude-3.5-sonnet
```
- Excellent response quality
- Great at following instructions
- ~$3/1M tokens
- Best for production

### Best Value (Paid)
```bash
OPENAI_MODEL=openai/gpt-4o-mini
```
- Very good quality
- Fast responses
- Only $0.15/1M tokens
- Great balance

---

## FAQ

### Q: Do I need a credit card?
**A:** No! Free tier requires no payment method.

### Q: Will embeddings work?
**A:** Not needed! System uses text search instead (works great).

### Q: How many requests can I make?
**A:** Free tier: ~200/day per model. Paid: based on credits.

### Q: Can I switch models later?
**A:** Yes! Just update .env and restart workers.

### Q: Is OpenRouter reliable?
**A:** Yes! Used by thousands of developers. 99.9% uptime.

### Q: Can I use my own OpenAI key later?
**A:** Yes! Just change OPENAI_BASE_URL to empty and use OpenAI key.

---

## Next Steps

1. ✅ Get OpenRouter API key
2. ✅ Update .env file
3. ✅ Restart services
4. ✅ Test ticket creation
5. 📊 Monitor usage at https://openrouter.ai/activity
6. 🚀 Deploy to production (see DEPLOYMENT.md)

---

## Support

- **OpenRouter Docs:** https://openrouter.ai/docs
- **Model List:** https://openrouter.ai/models
- **Discord:** https://discord.gg/openrouter
- **This Project:** See QUICKSTART.md, TEST_REPORT.md

---

**Last Updated:** 2026-02-22
**Status:** ✅ Tested and Working
**Cost:** $0/month (free tier) or $5-20/month (paid)
