# Operational Runbooks - Customer Success Digital FTE

## Table of Contents

1. [Common Operations](#common-operations)
2. [Troubleshooting](#troubleshooting)
3. [Incident Response](#incident-response)
4. [Deployment Procedures](#deployment-procedures)
5. [Backup and Recovery](#backup-and-recovery)
6. [Monitoring and Alerts](#monitoring-and-alerts)

---

## Common Operations

### Starting the System

**Local Development:**
```bash
# Start infrastructure
docker-compose up -d

# Wait for services
sleep 10

# Check health
curl http://localhost:8000/health

# Start API
uvicorn src.api.main:app --reload --port 8000

# Start worker (in another terminal)
python -m src.worker.kafka_consumer
```

**Production (Kubernetes):**
```bash
# Deploy all services
kubectl apply -f k8s/deployment.yaml

# Check deployment status
kubectl get pods -n customer-success-fte

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod -l app=fte-api -n customer-success-fte --timeout=300s
kubectl wait --for=condition=ready pod -l app=fte-worker -n customer-success-fte --timeout=300s

# Check health
kubectl port-forward service/fte-api-service 8000:80 -n customer-success-fte
curl http://localhost:8000/health
```

### Stopping the System

**Local Development:**
```bash
# Stop API and worker (Ctrl+C in terminals)

# Stop infrastructure
docker-compose down
```

**Production (Kubernetes):**
```bash
# Scale down to zero (preserves configuration)
kubectl scale deployment fte-api --replicas=0 -n customer-success-fte
kubectl scale deployment fte-worker --replicas=0 -n customer-success-fte

# Or delete everything
kubectl delete -f k8s/deployment.yaml
```

### Scaling Operations

**Manual Scaling:**
```bash
# Scale API pods
kubectl scale deployment fte-api --replicas=5 -n customer-success-fte

# Scale worker pods
kubectl scale deployment fte-worker --replicas=5 -n customer-success-fte

# Verify scaling
kubectl get pods -n customer-success-fte
```

**Check Auto-scaling Status:**
```bash
# View HPA status
kubectl get hpa -n customer-success-fte

# Describe HPA for details
kubectl describe hpa fte-api-hpa -n customer-success-fte
kubectl describe hpa fte-worker-hpa -n customer-success-fte
```

### Viewing Logs

**Local Development:**
```bash
# API logs
docker-compose logs -f api

# Worker logs
docker-compose logs -f worker

# All logs
docker-compose logs -f
```

**Production (Kubernetes):**
```bash
# API logs
kubectl logs -f deployment/fte-api -n customer-success-fte

# Worker logs
kubectl logs -f deployment/fte-worker -n customer-success-fte

# Specific pod logs
kubectl logs -f <pod-name> -n customer-success-fte

# Previous pod logs (if crashed)
kubectl logs --previous <pod-name> -n customer-success-fte

# Tail last 100 lines
kubectl logs --tail=100 deployment/fte-api -n customer-success-fte
```

### Database Operations

**Connect to Database:**
```bash
# Local
docker-compose exec postgres psql -U postgres -d customer_success_fte

# Kubernetes
kubectl exec -it deployment/postgres -n customer-success-fte -- psql -U postgres -d customer_success_fte
```

**Common Database Queries:**
```sql
-- Check total customers
SELECT COUNT(*) FROM customers;

-- Check active conversations
SELECT channel, COUNT(*) FROM conversations WHERE status = 'active' GROUP BY channel;

-- Check recent messages
SELECT created_at, channel, role, LEFT(content, 50) FROM messages ORDER BY created_at DESC LIMIT 10;

-- Check escalated tickets
SELECT id, created_at, escalation_reason, urgency FROM tickets WHERE escalated = true ORDER BY created_at DESC LIMIT 10;

-- Check knowledge base size
SELECT category, COUNT(*) FROM knowledge_base GROUP BY category;
```

**Database Backup:**
```bash
# Local
docker-compose exec postgres pg_dump -U postgres customer_success_fte > backup_$(date +%Y%m%d_%H%M%S).sql

# Kubernetes
kubectl exec deployment/postgres -n customer-success-fte -- pg_dump -U postgres customer_success_fte > backup_$(date +%Y%m%d_%H%M%S).sql
```

**Database Restore:**
```bash
# Local
cat backup_20260215_120000.sql | docker-compose exec -T postgres psql -U postgres -d customer_success_fte

# Kubernetes
cat backup_20260215_120000.sql | kubectl exec -i deployment/postgres -n customer-success-fte -- psql -U postgres -d customer_success_fte
```

### Kafka Operations

**List Topics:**
```bash
# Local
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Kubernetes
kubectl exec deployment/kafka -n customer-success-fte -- kafka-topics --list --bootstrap-server localhost:9092
```

**Check Consumer Lag:**
```bash
# Local
docker-compose exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group fte-workers

# Kubernetes
kubectl exec deployment/kafka -n customer-success-fte -- kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group fte-workers
```

**View Messages in Topic:**
```bash
# Local (last 10 messages)
docker-compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic fte.tickets.incoming --from-beginning --max-messages 10

# Kubernetes
kubectl exec deployment/kafka -n customer-success-fte -- kafka-console-consumer --bootstrap-server localhost:9092 --topic fte.tickets.incoming --from-beginning --max-messages 10
```

---

## Troubleshooting

### Issue: API Not Responding

**Symptoms:**
- Health check fails
- HTTP requests timeout
- 502/503 errors

**Diagnosis:**
```bash
# Check pod status
kubectl get pods -n customer-success-fte

# Check pod logs
kubectl logs deployment/fte-api -n customer-success-fte --tail=100

# Check resource usage
kubectl top pods -n customer-success-fte

# Check events
kubectl get events -n customer-success-fte --sort-by='.lastTimestamp'
```

**Resolution:**
1. Check if pods are running: `kubectl get pods -n customer-success-fte`
2. If pods are CrashLooping, check logs for errors
3. Common causes:
   - Database connection failure → Check DATABASE_URL
   - Kafka connection failure → Check KAFKA_BOOTSTRAP_SERVERS
   - Missing secrets → Check secrets are properly set
4. Restart pods: `kubectl rollout restart deployment/fte-api -n customer-success-fte`

### Issue: Worker Not Processing Messages

**Symptoms:**
- Messages stuck in Kafka queue
- High consumer lag
- No responses being sent

**Diagnosis:**
```bash
# Check worker pods
kubectl get pods -l app=fte-worker -n customer-success-fte

# Check worker logs
kubectl logs deployment/fte-worker -n customer-success-fte --tail=100

# Check consumer lag
kubectl exec deployment/kafka -n customer-success-fte -- kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group fte-workers
```

**Resolution:**
1. Check worker pod status
2. Check for errors in worker logs
3. Common causes:
   - OpenAI API key invalid → Check OPENAI_API_KEY secret
   - Database connection issues → Check DATABASE_URL
   - Kafka connection issues → Check KAFKA_BOOTSTRAP_SERVERS
4. Scale up workers if lag is high: `kubectl scale deployment fte-worker --replicas=5 -n customer-success-fte`
5. Restart workers: `kubectl rollout restart deployment/fte-worker -n customer-success-fte`

### Issue: High Escalation Rate

**Symptoms:**
- Escalation rate >25%
- Many tickets being escalated
- Customers not getting AI responses

**Diagnosis:**
```bash
# Check escalation metrics
curl http://localhost:8000/metrics | grep fte_agent_escalations_total

# Check recent escalations in database
kubectl exec deployment/postgres -n customer-success-fte -- psql -U postgres -d customer_success_fte -c "SELECT escalation_reason, COUNT(*) FROM tickets WHERE escalated = true GROUP BY escalation_reason;"
```

**Resolution:**
1. Review escalation reasons in database
2. Common causes:
   - Knowledge base gaps → Add more articles
   - Overly sensitive escalation triggers → Adjust escalation logic
   - Complex questions → Improve agent prompts
3. Update knowledge base: `python scripts/load_knowledge_base.py`
4. Review and adjust escalation keywords in agent code

### Issue: Slow Response Times

**Symptoms:**
- P95 response time >3 seconds
- Customers complaining about delays
- High processing duration metrics

**Diagnosis:**
```bash
# Check response time metrics
curl http://localhost:8000/metrics | grep fte_agent_processing_duration_seconds

# Check database query performance
kubectl exec deployment/postgres -n customer-success-fte -- psql -U postgres -d customer_success_fte -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Check OpenAI API latency in logs
kubectl logs deployment/fte-worker -n customer-success-fte | grep "OpenAI"
```

**Resolution:**
1. Check database indexes are created
2. Optimize slow queries
3. Consider caching common responses
4. Scale up workers if needed
5. Check OpenAI API status: https://status.openai.com

### Issue: High Costs

**Symptoms:**
- Daily cost >$3
- Monthly projection >$1,000
- High token usage

**Diagnosis:**
```bash
# Check cost metrics
curl http://localhost:8000/metrics | grep fte_estimated_cost_dollars

# Check token usage
curl http://localhost:8000/metrics | grep fte_openai_tokens_used_total

# Check message volume
curl http://localhost:8000/metrics | grep fte_agent_messages_processed_total
```

**Resolution:**
1. Review token usage patterns
2. Optimize prompts to reduce token count
3. Implement response caching for common questions
4. Consider using smaller model for simple queries
5. Review and optimize knowledge base search

### Issue: Database Connection Pool Exhausted

**Symptoms:**
- "Too many connections" errors
- Slow database queries
- API timeouts

**Diagnosis:**
```bash
# Check active connections
kubectl exec deployment/postgres -n customer-success-fte -- psql -U postgres -d customer_success_fte -c "SELECT count(*) FROM pg_stat_activity;"

# Check connection pool settings
kubectl exec deployment/postgres -n customer-success-fte -- psql -U postgres -d customer_success_fte -c "SHOW max_connections;"
```

**Resolution:**
1. Increase max_connections in PostgreSQL config
2. Adjust connection pool size in application
3. Check for connection leaks in code
4. Scale up database if needed

---

## Incident Response

### Severity Levels

**P0 - Critical (Response: Immediate)**
- Complete system outage
- Data loss
- Security breach

**P1 - High (Response: <1 hour)**
- Partial system outage
- High error rate (>10%)
- Escalation rate >50%

**P2 - Medium (Response: <4 hours)**
- Performance degradation
- Single channel down
- Escalation rate 25-50%

**P3 - Low (Response: <24 hours)**
- Minor issues
- Non-critical bugs
- Feature requests

### Incident Response Procedure

1. **Detect**: Alert fires or user reports issue
2. **Assess**: Determine severity level
3. **Notify**: Alert on-call engineer
4. **Investigate**: Use troubleshooting runbooks
5. **Mitigate**: Apply temporary fix if needed
6. **Resolve**: Implement permanent fix
7. **Document**: Write incident report
8. **Review**: Post-mortem meeting

### Emergency Contacts

- On-call Engineer: [Phone/Slack]
- OpenAI Support: https://help.openai.com
- Twilio Support: https://www.twilio.com/help/contact
- Database Admin: [Contact]

### Rollback Procedure

```bash
# Kubernetes rollback
kubectl rollout undo deployment/fte-api -n customer-success-fte
kubectl rollout undo deployment/fte-worker -n customer-success-fte

# Check rollback status
kubectl rollout status deployment/fte-api -n customer-success-fte
```

---

## Deployment Procedures

### Pre-Deployment Checklist

- [ ] All tests passing (unit, integration, E2E)
- [ ] Load testing completed
- [ ] Database migrations tested
- [ ] Secrets updated if needed
- [ ] Rollback plan prepared
- [ ] Stakeholders notified
- [ ] Monitoring dashboards ready

### Deployment Steps

1. **Build and tag images:**
```bash
docker build -f Dockerfile.api -t customer-success-fte-api:v1.2.0 .
docker build -f Dockerfile.worker -t customer-success-fte-worker:v1.2.0 .
docker push customer-success-fte-api:v1.2.0
docker push customer-success-fte-worker:v1.2.0
```

2. **Update Kubernetes manifests:**
```bash
# Update image tags in k8s/deployment.yaml
sed -i 's/customer-success-fte-api:latest/customer-success-fte-api:v1.2.0/g' k8s/deployment.yaml
sed -i 's/customer-success-fte-worker:latest/customer-success-fte-worker:v1.2.0/g' k8s/deployment.yaml
```

3. **Apply changes:**
```bash
kubectl apply -f k8s/deployment.yaml
```

4. **Monitor rollout:**
```bash
kubectl rollout status deployment/fte-api -n customer-success-fte
kubectl rollout status deployment/fte-worker -n customer-success-fte
```

5. **Verify deployment:**
```bash
# Check health
curl https://support.techcorp.com/health

# Check metrics
curl https://support.techcorp.com/metrics | grep fte_agent_messages_processed_total

# Monitor logs
kubectl logs -f deployment/fte-api -n customer-success-fte
```

6. **Post-deployment verification:**
- Submit test support request
- Verify response received
- Check escalation flow
- Monitor error rates for 30 minutes

### Post-Deployment Checklist

- [ ] All pods running
- [ ] Health checks passing
- [ ] No error spikes in logs
- [ ] Metrics look normal
- [ ] Test requests successful
- [ ] Stakeholders notified of completion

---

## Backup and Recovery

### Automated Backups

**Database Backup CronJob:**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: customer-success-fte
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:16
            command:
            - /bin/sh
            - -c
            - pg_dump -h postgres-service -U postgres customer_success_fte | gzip > /backups/backup-$(date +%Y%m%d).sql.gz
            volumeMounts:
            - name: backup-storage
              mountPath: /backups
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

### Manual Backup

```bash
# Full database backup
kubectl exec deployment/postgres -n customer-success-fte -- pg_dump -U postgres customer_success_fte | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Backup specific tables
kubectl exec deployment/postgres -n customer-success-fte -- pg_dump -U postgres -t customers -t conversations -t messages customer_success_fte > backup_core_tables.sql
```

### Recovery Procedures

**Full Database Restore:**
```bash
# Stop workers to prevent new writes
kubectl scale deployment fte-worker --replicas=0 -n customer-success-fte

# Restore database
gunzip < backup_20260215_020000.sql.gz | kubectl exec -i deployment/postgres -n customer-success-fte -- psql -U postgres -d customer_success_fte

# Restart workers
kubectl scale deployment fte-worker --replicas=2 -n customer-success-fte
```

**Point-in-Time Recovery:**
```bash
# Requires WAL archiving enabled
# Restore to specific timestamp
kubectl exec deployment/postgres -n customer-success-fte -- pg_restore --target-time='2026-02-15 12:00:00'
```

---

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Availability**: Uptime >99.9%
2. **Performance**: P95 response time <3s
3. **Quality**: Escalation rate <25%
4. **Cost**: Daily cost <$3

### Alert Rules

**Critical Alerts (P0):**
- API down for >5 minutes
- Database down
- Kafka down
- Error rate >50%

**High Priority Alerts (P1):**
- P95 response time >5s for >10 minutes
- Escalation rate >40%
- Worker lag >1000 messages
- Error rate >10%

**Medium Priority Alerts (P2):**
- P95 response time >3s for >30 minutes
- Escalation rate >25%
- Daily cost >$5
- Disk usage >80%

### Prometheus Alert Rules

```yaml
groups:
- name: fte_alerts
  rules:
  - alert: HighEscalationRate
    expr: sum(fte_agent_escalations_total) / sum(fte_agent_messages_processed_total) > 0.25
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High escalation rate detected"
      description: "Escalation rate is {{ $value | humanizePercentage }}"

  - alert: SlowResponseTime
    expr: histogram_quantile(0.95, rate(fte_agent_processing_duration_seconds_bucket[5m])) > 3
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Slow response time detected"
      description: "P95 response time is {{ $value }}s"

  - alert: HighCost
    expr: increase(fte_estimated_cost_dollars[24h]) > 5
    labels:
      severity: warning
    annotations:
      summary: "Daily cost exceeds threshold"
      description: "Daily cost is ${{ $value }}"
```

---

## Maintenance Windows

### Scheduled Maintenance

**Frequency**: Monthly (first Sunday, 2-4 AM UTC)

**Procedure:**
1. Notify users 48 hours in advance
2. Scale down to maintenance mode
3. Perform updates
4. Run health checks
5. Scale back up
6. Monitor for 1 hour
7. Notify users of completion

### Emergency Maintenance

Follow incident response procedure with P1 severity.
