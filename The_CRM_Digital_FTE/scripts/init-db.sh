#!/bin/bash
# Database initialization script
# Run this after PostgreSQL is up to set up the schema

set -e

echo "Initializing Customer Success FTE database..."

# Wait for PostgreSQL to be ready
until PGPASSWORD=$DATABASE_PASSWORD psql -h "$DATABASE_HOST" -U "$DATABASE_USER" -d "$DATABASE_NAME" -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - executing schema"

# Run schema creation
PGPASSWORD=$DATABASE_PASSWORD psql -h "$DATABASE_HOST" -U "$DATABASE_USER" -d "$DATABASE_NAME" -f /app/src/database/schema.sql

echo "Database schema created successfully"

# Create Kafka topics
echo "Creating Kafka topics..."

kafka-topics --create \
  --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" \
  --topic fte.tickets.incoming \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

kafka-topics --create \
  --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" \
  --topic fte.escalations \
  --partitions 1 \
  --replication-factor 1 \
  --if-not-exists

kafka-topics --create \
  --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" \
  --topic fte.metrics \
  --partitions 1 \
  --replication-factor 1 \
  --if-not-exists

kafka-topics --create \
  --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" \
  --topic fte.dlq \
  --partitions 1 \
  --replication-factor 1 \
  --if-not-exists

echo "Kafka topics created successfully"

echo "Initialization complete!"
