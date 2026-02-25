# Operational Runbook - Customer Success Digital FTE

## Overview

This runbook provides step-by-step procedures for operating and troubleshooting the Customer Success Digital FTE system in production.

## On-Call Responsibilities

### Primary Responsibilities
- Monitor system health and alerts
- Respond to incidents within SLA
- Escalate critical issues
- Document all incidents

### SLA Targets
- **P0 (Critical)**: 15 minutes response, 1 hour resolution
- **P1 (High)**: 30 minutes response, 4 hours resolution
- **P2 (Medium)**: 2 hours response, 24 hours resolution
- **P3 (Low)**: 1 business day response

## Common Incidents and Resolutions

### Incident 1: API Pods Crashing

**Symptoms:**
- Health check failures
- 503 errors from load balancer
- Prometheus alert: `APIPodDown`

**Diagnosis:**
```bash
# Check pod status
kubectl get pods -n customer-success-fte -l component=api

# View recent events
kubectl get events -n customer-success-fte --sort-by='.lastTimestamp' | tail -20

# Check logs
kubectl logs -n customer-success-fte -l component=api --tail=100
```

**Common Causes:**
1. **Out of Memory (OOMKilled)**
   - Check: `kubectl describe pod <pod-name> -n customer-success-fte | grep -A 5 "Last State"`
   - Fix: Increase memory limits in deployment-api.yaml
   ```bash
   kubectl set resources deployment/fte-api -n customer-success-fte \
     --limits=memory=2Gi --requests=memory=1Gi
   ```

2. **Database Connection Failure**
   - Check: `kubectl logs -n customer-success-fte -l component=api | grep -i "database"`
   - Fix: Verify DATABASE_URL secret is correct
   ```bash
   kubectl get secret fte-secrets -n customer-success-fte -o jsonpath='{.data.DATABASE_URL}' | base64 -d
   ```

3. **Missing Environment Variables**
   - Check: `kubectl describe pod <pod-name> -n customer-success-fte | grep -A 20 "Environment"`
   - Fix: Update secrets or configmap and restart pods

**Resolution Steps:**
1. Identify root cause from logs
2. Apply fix (increase resources, fix config, etc.)
3. Restart deployment if needed:
   ```bash
   kubectl rollout restart deployment/fte-api -n customer-success-fte
   ```
4. Monitor recovery:
   ```bash
   kubectl rollout status deployment/fte-api -n customer-success-fte
   ```
5. Verify health:
   ```bash
   curl https://your-domain/health
   ```

---

### Incident 2: Workers Not Processing Messages

**Symptoms:**
- Messages accumulating in Kafka
- No responses being sent to customers
- Prometheus alert: `KafkaConsumerLag`

**Diagnosis:**
```bash
# Check worker pods
kubectl get pods -n customer-success-fte -l component=worker

# Check worker logs
kubectl logs -n customer-success-fte -l component=worker --tail=100

# Check Kafka consumer lag
kubectl exec -it kafka-0 -n customer-success-fte -- \
  kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --describe --group fte-workers
```

**Common Causes:**
1. **Worker Pods Crashed**
   - Check: Pod status shows CrashLoopBackOff
   - Fix: Check logs for errors, fix configuration, restart

2. **Kafka Connection Lost**
   - Check: Logs show "Failed to connect to Kafka"
   - Fix: Verify Kafka is running and accessible
   ```bash
   kubectl get pods -n customer-success-fte -l app=kafka
   kubectl logs -n customer-success-fte -l app=kafka --tail=50
   ```

3. **OpenAI API Rate Limit**
   - Check: Logs show "Rate limit exceeded"
   - Fix: Implement exponential backoff (already in code) or upgrade OpenAI tier

4. **Database Connection Pool Exhausted**
   - Check: Logs show "Connection pool exhausted"
   - Fix: Increase connection pool size or scale workers

**Resolution Steps:**
1. Restart worker pods:
   ```bash
   kubectl rollout restart deployment/fte-worker -n customer-success-fte
   ```
2. If lag is high, scale up workers:
   ```bash
   kubectl scale deployment/fte-worker -n customer-success-fte --replicas=5
   ```
3. Monitor processing:
   ```bash
   kubectl logs -n customer-success-fte -l component=worker -f | grep "Processed message"
   ```
4. Verify lag is decreasing:
   ```bash
   # Check consumer lag every 30 seconds
   watch -n 30 'kubectl exec -it kafka-0 -n customer-success-fte -- \
     kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
     --describe --group fte-workers'
   ```

---

### Incident 3: High Response Latency

**Symptoms:**
- P95 latency > 3 seconds
- Customer complaints about slow responses
- Prometheus alert: `HighLatency`

**Diagnosis:**
```bash
# Check current latency
curl https://your-domain/metrics | grep http_request_duration_seconds

# Check resource usage
kubectl top pods -n customer-success-fte

# Check database performance
kubectl exec -it postgres-0 -n customer-success-fte -- psql -U fte_user -d customer_success_fte -c "
  SELECT query, calls, mean_exec_time, max_exec_time
  FROM pg_stat_statements
  ORDER BY mean_exec_time DESC
  LIMIT 10;"
```

**Common Causes:**
1. **Insufficient Resources**
   - Check: CPU/Memory usage near limits
   - Fix: Scale horizontally or increase resource limits

2. **Slow Database Queries**
   - Check: pg_stat_statements shows slow queries
   - Fix: Add indexes, optimize queries
   ```sql
   -- Example: Add index for common query
   CREATE INDEX CONCURRENTLY idx_messages_conversation_created
     ON messages(conversation_id, created_at DESC);
   ```

3. **OpenAI API Slow**
   - Check: Logs show high OpenAI response times
   - Fix: Use faster model (gpt-4o-mini) or implement caching

4. **Too Many Concurrent Requests**
   - Check: High request rate in metrics
   - Fix: Scale API pods
   ```bash
   kubectl scale deployment/fte-api -n customer-success-fte --replicas=10
   ```

**Resolution Steps:**
1. Identify bottleneck (CPU, memory, database, external API)
2. Apply appropriate fix:
   - Scale pods: `kubectl scale deployment/fte-api --replicas=N`
   - Optimize database: Add indexes, tune queries
   - Increase resources: Update deployment limits
3. Monitor latency improvement:
   ```bash
   watch -n 5 'curl -s https://your-domain/metrics | grep -A 5 http_request_duration_seconds'
   ```

---

### Incident 4: Database Connection Failures

**Symptoms:**
- API returns 500 errors
- Logs show "Cannot connect to database"
- Prometheus alert: `DatabaseConnectionFailed`

**Diagnosis:**
```bash
# Check database pod
kubectl get pods -n customer-success-fte -l app=postgres

# Check database logs
kubectl logs -n customer-success-fte -l app=postgres --tail=100

# Test connection from API pod
kubectl exec -it <api-pod-name> -n customer-success-fte -- \
  psql "$DATABASE_URL" -c "SELECT 1"
```

**Common Causes:**
1. **Database Pod Down**
   - Check: Pod status
   - Fix: Restart database pod (data should persist in PVC)
   ```bash
   kubectl rollout restart statefulset/postgres -n customer-success-fte
   ```

2. **Connection String Incorrect**
   - Check: Verify DATABASE_URL secret
   - Fix: Update secret with correct connection string

3. **Connection Pool Exhausted**
   - Check: Logs show "Too many connections"
   - Fix: Increase max_connections in PostgreSQL config

4. **Network Policy Blocking**
   - Check: Network policies
   - Fix: Update network policy to allow API -> DB traffic

**Resolution Steps:**
1. Verify database is running:
   ```bash
   kubectl get pods -n customer-success-fte -l app=postgres
   ```
2. Test connection:
   ```bash
   kubectl exec -it postgres-0 -n customer-success-fte -- \
     psql -U fte_user -d customer_success_fte -c "SELECT version();"
   ```
3. If database is down, check PVC and restart:
   ```bash
   kubectl get pvc -n customer-success-fte
   kubectl rollout restart statefulset/postgres -n customer-success-fte
   ```
4. Restart API pods to reconnect:
   ```bash
   kubectl rollout restart deployment/fte-api -n customer-success-fte
   ```

---

### Incident 5: Kafka Messages Not Being Consumed

**Symptoms:**
- Messages stuck in Kafka topics
- Consumer lag increasing
- No ticket processing

**Diagnosis:**
```bash
# Check Kafka topics
kubectl exec -it kafka-0 -n customer-success-fte -- \
  kafka-topics.sh --bootstrap-server localhost:9092 --list

# Check message count in topic
kubectl exec -it kafka-0 -n customer-success-fte -- \
  kafka-run-class.sh kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic fte.tickets.incoming

# Check consumer groups
kubectl exec -it kafka-0 -n customer-success-fte -- \
  kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list
```

**Common Causes:**
1. **No Active Consumers**
   - Check: Worker pods not running
   - Fix: Start worker pods

2. **Consumer Group Stuck**
   - Check: Consumer lag not decreasing
   - Fix: Reset consumer group offset
   ```bash
   kubectl exec -it kafka-0 -n customer-success-fte -- \
     kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
     --group fte-workers --reset-offsets --to-latest --execute \
     --topic fte.tickets.incoming
   ```

3. **Kafka Broker Down**
   - Check: Kafka pod status
   - Fix: Restart Kafka

**Resolution Steps:**
1. Verify Kafka is healthy
2. Verify workers are running and connected
3. Check consumer group status
4. Reset offsets if needed (CAUTION: may lose messages)
5. Scale workers if lag is high

---

## Monitoring and Alerts

### Critical Alerts

| Alert | Severity | Response Time | Action |
|-------|----------|---------------|--------|
| APIPodDown | Critical | 15 min | Restart pods, check logs |
| DatabaseConnectionFailed | Critical | 15 min | Check DB, restart if needed |
| KafkaConnectionFailed | Critical | 15 min | Check Kafka, restart if needed |
| HighErrorRate | High | 30 min | Check logs, identify root cause |
| HighLatency | High | 30 min | Scale pods, optimize queries |
| HighEscalationRate | Medium | 2 hours | Review agent prompts |

### Metrics to Monitor

**System Health:**
- `up{job="fte-api"}` - API pod health
- `database_health` - Database connection status
- `kafka_health` - Kafka connection status

**Performance:**
- `http_request_duration_seconds` - API latency
- `messages_processed_total` - Message throughput
- `kafka_consumer_lag` - Consumer lag

**Business Metrics:**
- `tickets_created_total` - Ticket creation rate
- `tickets_escalated_total` - Escalation rate
- `customer_satisfaction_score` - CSAT (if implemented)

---

## Maintenance Procedures

### Rolling Update

```bash
# Update image
kubectl set image deployment/fte-api \
  fte-api=your-registry/customer-success-fte:v2.0.0 \
  -n customer-success-fte

# Monitor rollout
kubectl rollout status deployment/fte-api -n customer-success-fte

# Rollback if issues
kubectl rollout undo deployment/fte-api -n customer-success-fte
```

### Database Maintenance

```bash
# Vacuum and analyze
kubectl exec -it postgres-0 -n customer-success-fte -- \
  psql -U fte_user -d customer_success_fte -c "VACUUM ANALYZE;"

# Reindex
kubectl exec -it postgres-0 -n customer-success-fte -- \
  psql -U fte_user -d customer_success_fte -c "REINDEX DATABASE customer_success_fte;"
```

### Kafka Maintenance

```bash
# Check disk usage
kubectl exec -it kafka-0 -n customer-success-fte -- df -h

# Clean up old logs (if retention policy not working)
kubectl exec -it kafka-0 -n customer-success-fte -- \
  kafka-configs.sh --bootstrap-server localhost:9092 \
  --entity-type topics --entity-name fte.tickets.incoming \
  --alter --add-config retention.ms=604800000  # 7 days
```

---

## Escalation Procedures

### Level 1: On-Call Engineer
- Handle common incidents
- Follow runbook procedures
- Escalate if unresolved in 1 hour

### Level 2: Senior Engineer
- Complex issues requiring deep system knowledge
- Performance optimization
- Architecture changes

### Level 3: Engineering Manager
- Critical business impact
- Multi-system failures
- Vendor escalations (OpenAI, Twilio, etc.)

### Escalation Contacts
- L2: senior-engineer@company.com
- L3: engineering-manager@company.com
- Vendor Support: See vendor documentation

---

## Post-Incident Procedures

### Incident Report Template

```markdown
# Incident Report: [Brief Description]

**Date:** YYYY-MM-DD
**Duration:** X hours
**Severity:** P0/P1/P2/P3
**Impact:** [Number of affected customers, downtime, etc.]

## Timeline
- HH:MM - Incident detected
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Fix applied
- HH:MM - Incident resolved

## Root Cause
[Detailed explanation of what caused the incident]

## Resolution
[What was done to resolve the incident]

## Prevention
[What will be done to prevent this in the future]

## Action Items
- [ ] Action 1 (Owner: Name, Due: Date)
- [ ] Action 2 (Owner: Name, Due: Date)
```

### Post-Mortem Meeting
- Schedule within 48 hours of major incidents
- Include all stakeholders
- Focus on learning, not blame
- Document action items

---

## Emergency Contacts

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| On-Call Engineer | Rotation | PagerDuty | 24/7 |
| Senior Engineer | TBD | Email/Slack | Business hours |
| Engineering Manager | TBD | Email/Phone | Business hours |
| OpenAI Support | - | platform.openai.com/support | 24/7 |
| Twilio Support | - | support.twilio.com | 24/7 |

---

## Useful Commands Reference

### Quick Health Check
```bash
# All-in-one health check
kubectl get pods -n customer-success-fte && \
curl -s https://your-domain/health | jq && \
kubectl top pods -n customer-success-fte
```

### View All Logs
```bash
# Stream all logs
kubectl logs -n customer-success-fte --all-containers=true -f --max-log-requests=10
```

### Emergency Scale Down (Cost Savings)
```bash
# Scale to minimum
kubectl scale deployment/fte-api -n customer-success-fte --replicas=1
kubectl scale deployment/fte-worker -n customer-success-fte --replicas=1
```

### Emergency Scale Up (High Load)
```bash
# Scale to maximum
kubectl scale deployment/fte-api -n customer-success-fte --replicas=10
kubectl scale deployment/fte-worker -n customer-success-fte --replicas=10
```

---

## Additional Resources

- **Architecture Diagram**: See DEPLOYMENT.md
- **API Documentation**: https://your-domain/docs
- **Grafana Dashboards**: https://grafana.your-domain
- **Prometheus Alerts**: https://prometheus.your-domain
- **Incident History**: [Link to incident tracking system]
