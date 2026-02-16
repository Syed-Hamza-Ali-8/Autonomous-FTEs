# Deployment Guide - Customer Success Digital FTE

## Prerequisites

- Docker and Docker Compose
- Kubernetes cluster (local: minikube/kind, cloud: GKE/EKS/AKS)
- kubectl configured
- OpenAI API key
- Twilio account (for WhatsApp)
- Gmail API credentials (for email)

## Local Development Setup

### 1. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:
- `OPENAI_API_KEY`: Your OpenAI API key
- `TWILIO_ACCOUNT_SID`: Your Twilio account SID
- `TWILIO_AUTH_TOKEN`: Your Twilio auth token
- `TWILIO_WHATSAPP_NUMBER`: Your Twilio WhatsApp number
- `GMAIL_CREDENTIALS_PATH`: Path to Gmail OAuth credentials

### 2. Start Infrastructure

Start PostgreSQL, Kafka, Redis, Prometheus, and Grafana:
```bash
docker-compose up -d
```

Wait for services to be ready:
```bash
docker-compose ps
```

### 3. Initialize Database

Run the database schema:
```bash
docker-compose exec postgres psql -U postgres -d customer_success_fte -f /docker-entrypoint-initdb.d/schema.sql
```

Or use the initialization script:
```bash
chmod +x scripts/init-db.sh
./scripts/init-db.sh
```

### 4. Load Knowledge Base

Populate the knowledge base with product documentation:
```bash
python scripts/load_knowledge_base.py
```

### 5. Run the Application

Start the API server:
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Start the Kafka worker (in another terminal):
```bash
python -m src.worker.kafka_consumer
```

### 6. Access the Application

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

## Production Deployment (Kubernetes)

### 1. Build Docker Images

Build the API image:
```bash
docker build -f Dockerfile.api -t customer-success-fte-api:latest .
```

Build the worker image:
```bash
docker build -f Dockerfile.worker -t customer-success-fte-worker:latest .
```

Tag and push to your container registry:
```bash
docker tag customer-success-fte-api:latest your-registry/customer-success-fte-api:latest
docker push your-registry/customer-success-fte-api:latest

docker tag customer-success-fte-worker:latest your-registry/customer-success-fte-worker:latest
docker push your-registry/customer-success-fte-worker:latest
```

### 2. Update Kubernetes Secrets

Create base64-encoded secrets:
```bash
echo -n "your-openai-key" | base64
echo -n "your-twilio-sid" | base64
echo -n "your-twilio-token" | base64
echo -n "your-db-password" | base64
```

Update `k8s/deployment.yaml` with your encoded secrets.

### 3. Deploy to Kubernetes

Create the namespace and deploy:
```bash
kubectl apply -f k8s/deployment.yaml
```

Check deployment status:
```bash
kubectl get pods -n customer-success-fte
kubectl get services -n customer-success-fte
```

### 4. Initialize Database in Kubernetes

Run the initialization job:
```bash
kubectl run init-db --image=customer-success-fte-api:latest \
  --namespace=customer-success-fte \
  --restart=Never \
  --command -- /bin/bash /app/scripts/init-db.sh
```

Check logs:
```bash
kubectl logs init-db -n customer-success-fte
```

### 5. Load Knowledge Base

Create a job to load the knowledge base:
```bash
kubectl run load-kb --image=customer-success-fte-api:latest \
  --namespace=customer-success-fte \
  --restart=Never \
  --command -- python /app/scripts/load_knowledge_base.py
```

### 6. Configure Webhooks

Get the external IP of your API service:
```bash
kubectl get service fte-api-service -n customer-success-fte
```

Configure webhooks:
- **Gmail**: Set up Pub/Sub push notifications to `https://your-domain/webhooks/gmail`
- **WhatsApp**: Configure Twilio webhook to `https://your-domain/webhooks/whatsapp`

### 7. Monitor the Deployment

View logs:
```bash
# API logs
kubectl logs -f deployment/fte-api -n customer-success-fte

# Worker logs
kubectl logs -f deployment/fte-worker -n customer-success-fte
```

Check metrics:
```bash
kubectl port-forward service/fte-api-service 8000:80 -n customer-success-fte
# Visit http://localhost:8000/metrics
```

## Scaling

### Manual Scaling

Scale API pods:
```bash
kubectl scale deployment fte-api --replicas=5 -n customer-success-fte
```

Scale worker pods:
```bash
kubectl scale deployment fte-worker --replicas=5 -n customer-success-fte
```

### Auto-scaling

HPA is configured to scale based on CPU and memory:
- API: 2-10 replicas (70% CPU, 80% memory)
- Worker: 2-10 replicas (70% CPU, 80% memory)

Check HPA status:
```bash
kubectl get hpa -n customer-success-fte
```

## Monitoring

### Prometheus Metrics

Key metrics to monitor:
- `fte_agent_messages_processed_total`: Total messages processed
- `fte_agent_processing_duration_seconds`: Processing time
- `fte_agent_escalations_total`: Escalation rate
- `fte_http_request_duration_seconds`: API response time
- `fte_openai_tokens_used_total`: Token usage
- `fte_estimated_cost_dollars`: Cost tracking

### Grafana Dashboards

Import the provided Grafana dashboard:
```bash
kubectl port-forward service/grafana 3000:3000 -n customer-success-fte
```

Visit http://localhost:3000 and import `monitoring/grafana-dashboard.json`

## Troubleshooting

### Database Connection Issues

Check PostgreSQL status:
```bash
kubectl exec -it deployment/postgres -n customer-success-fte -- psql -U postgres -d customer_success_fte -c "SELECT 1"
```

### Kafka Connection Issues

Check Kafka topics:
```bash
kubectl exec -it deployment/kafka -n customer-success-fte -- kafka-topics --list --bootstrap-server localhost:9092
```

### Worker Not Processing Messages

Check worker logs:
```bash
kubectl logs -f deployment/fte-worker -n customer-success-fte
```

Check Kafka consumer lag:
```bash
kubectl exec -it deployment/kafka -n customer-success-fte -- kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group fte-workers
```

### High Escalation Rate

Check escalation metrics:
```bash
curl http://localhost:8000/metrics | grep fte_agent_escalations_total
```

Review escalation reasons in logs and adjust agent prompts if needed.

## Cost Optimization

### Target: <$1,000/year

Current cost breakdown:
- OpenAI API: ~$800/year (gpt-4o-mini, 10K messages/month)
- Twilio WhatsApp: ~$50/year (1K messages/month)
- Gmail API: Free
- Infrastructure: ~$150/year (minimal Kubernetes cluster)

Tips to reduce costs:
1. Use gpt-4o-mini for all responses (already configured)
2. Implement response caching for common questions
3. Use smaller embeddings (text-embedding-3-small, already configured)
4. Optimize prompts to reduce token usage
5. Use Kubernetes spot instances for workers

## Security

### Best Practices

1. **Secrets Management**: Use Kubernetes secrets or external secret managers (AWS Secrets Manager, HashiCorp Vault)
2. **Network Policies**: Restrict pod-to-pod communication
3. **RBAC**: Configure role-based access control
4. **TLS**: Enable TLS for all external endpoints
5. **API Authentication**: Add API key authentication for webhooks
6. **Rate Limiting**: Implement rate limiting on API endpoints

### Webhook Security

Validate webhook signatures:
- Gmail: Verify Pub/Sub JWT tokens
- WhatsApp: Verify Twilio signatures (already implemented)

## Backup and Recovery

### Database Backups

Create a CronJob for daily backups:
```bash
kubectl create cronjob postgres-backup \
  --image=postgres:16 \
  --schedule="0 2 * * *" \
  --namespace=customer-success-fte \
  -- pg_dump -h postgres-service -U postgres customer_success_fte > /backups/backup-$(date +%Y%m%d).sql
```

### Disaster Recovery

1. Database: Restore from latest backup
2. Kafka: Messages are ephemeral, no backup needed
3. Knowledge Base: Reload from source files

## Performance Tuning

### Database Optimization

1. Create indexes on frequently queried columns
2. Use connection pooling (already configured)
3. Enable query caching

### Kafka Optimization

1. Increase partitions for higher throughput
2. Tune consumer batch size
3. Enable compression (already configured)

### API Optimization

1. Enable response caching
2. Use async database queries (already implemented)
3. Implement request batching

## Support

For issues or questions:
- Check logs: `kubectl logs -f deployment/fte-api -n customer-success-fte`
- Review metrics: http://your-domain/metrics
- Check health: http://your-domain/health
