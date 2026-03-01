# Quick Test Commands

## Start Backend (Docker)
```bash
# Option 1: Use the test script
./start-test.sh        # Linux/Mac
start-test.bat         # Windows

# Option 2: Manual start
docker-compose up -d
docker-compose ps
curl http://localhost:8002/health
```

## Start Frontend (Next.js)
```bash
cd web
npm install           # First time only
npm run dev
```

Then open: http://localhost:3000/support

## Verify Tickets
```bash
# Connect to database
docker exec -it crm_fte_postgres psql -U fte_user -d customer_success_fte

# Query tickets
SELECT id, subject, status, created_at FROM tickets ORDER BY created_at DESC LIMIT 5;

# Exit
\q
```

## View Logs
```bash
docker-compose logs -f api worker
```

## Stop Everything
```bash
docker-compose down
# Press Ctrl+C in the terminal running npm run dev
```

## Troubleshooting

### Port 8002 already in use
```bash
# Find what's using it
lsof -i :8002              # Linux/Mac
netstat -ano | findstr :8002   # Windows

# Change port in docker-compose.yml if needed
```

### API not responding
```bash
docker-compose logs api
docker-compose restart api
```

### Database connection error
```bash
docker-compose logs postgres
docker exec -it crm_fte_postgres psql -U fte_user -d customer_success_fte -c "SELECT 1;"
```

### Frontend can't connect
Check `web/.env.local` contains:
```
NEXT_PUBLIC_API_URL=http://localhost:8002
```

## Quick Health Checks
```bash
# API Health
curl http://localhost:8002/health

# Database
docker exec -it crm_fte_postgres pg_isready -U fte_user

# Kafka
docker exec -it crm_fte_kafka kafka-topics --list --bootstrap-server localhost:9092

# All services
docker-compose ps
```
