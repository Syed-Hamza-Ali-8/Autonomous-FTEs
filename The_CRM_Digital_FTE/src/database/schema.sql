-- Customer Success FTE Database Schema
-- PostgreSQL 16 with pgvector extension
-- Phase 2: Specialization

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- ============================================================================
-- TABLE: customers
-- Unified customer records across all channels
-- ============================================================================
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT customers_email_or_phone_required CHECK (email IS NOT NULL OR phone IS NOT NULL)
);

-- Indexes for fast lookup
CREATE INDEX idx_customers_email ON customers(email) WHERE email IS NOT NULL;
CREATE INDEX idx_customers_phone ON customers(phone) WHERE phone IS NOT NULL;
CREATE INDEX idx_customers_created_at ON customers(created_at DESC);

-- ============================================================================
-- TABLE: customer_identifiers
-- Cross-channel customer identification
-- ============================================================================
CREATE TABLE customer_identifiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    identifier_type VARCHAR(50) NOT NULL, -- 'email', 'phone', 'whatsapp'
    identifier_value VARCHAR(255) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    UNIQUE(identifier_type, identifier_value)
);

-- Indexes
CREATE INDEX idx_customer_identifiers_customer_id ON customer_identifiers(customer_id);
CREATE INDEX idx_customer_identifiers_type_value ON customer_identifiers(identifier_type, identifier_value);

-- ============================================================================
-- TABLE: conversations
-- Conversation threads across channels
-- ============================================================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL, -- 'email', 'whatsapp', 'web_form'
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- 'active', 'resolved', 'escalated'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT conversations_channel_check CHECK (channel IN ('email', 'whatsapp', 'web_form')),
    CONSTRAINT conversations_status_check CHECK (status IN ('active', 'resolved', 'escalated'))
);

-- Indexes
CREATE INDEX idx_conversations_customer_id ON conversations(customer_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX idx_conversations_channel ON conversations(channel);

-- ============================================================================
-- TABLE: messages
-- All messages with channel metadata
-- ============================================================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- 'customer', 'agent', 'system'
    content TEXT NOT NULL,
    channel VARCHAR(50) NOT NULL,
    channel_message_id VARCHAR(255), -- External message ID (Gmail ID, Twilio SID, etc.)
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT messages_role_check CHECK (role IN ('customer', 'agent', 'system')),
    CONSTRAINT messages_channel_check CHECK (channel IN ('email', 'whatsapp', 'web_form'))
);

-- Indexes
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX idx_messages_channel_message_id ON messages(channel_message_id) WHERE channel_message_id IS NOT NULL;
CREATE INDEX idx_messages_role ON messages(role);

-- ============================================================================
-- TABLE: tickets
-- Support tickets
-- ============================================================================
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    subject VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'open', -- 'open', 'in_progress', 'resolved', 'escalated'
    priority VARCHAR(50) NOT NULL DEFAULT 'medium', -- 'low', 'medium', 'high'
    category VARCHAR(100) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    escalated_at TIMESTAMP WITH TIME ZONE,
    escalation_reason VARCHAR(255),
    assigned_to VARCHAR(255), -- Human agent email if escalated
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT tickets_status_check CHECK (status IN ('open', 'in_progress', 'resolved', 'escalated')),
    CONSTRAINT tickets_priority_check CHECK (priority IN ('low', 'medium', 'high')),
    CONSTRAINT tickets_channel_check CHECK (channel IN ('email', 'whatsapp', 'web_form'))
);

-- Indexes
CREATE INDEX idx_tickets_customer_id ON tickets(customer_id);
CREATE INDEX idx_tickets_conversation_id ON tickets(conversation_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_tickets_category ON tickets(category);
CREATE INDEX idx_tickets_created_at ON tickets(created_at DESC);
CREATE INDEX idx_tickets_channel ON tickets(channel);

-- ============================================================================
-- TABLE: knowledge_base
-- Product documentation with vector embeddings
-- ============================================================================
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    url VARCHAR(500),
    embedding VECTOR(1536), -- OpenAI text-embedding-3-small dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX idx_knowledge_base_category ON knowledge_base(category);
CREATE INDEX idx_knowledge_base_embedding ON knowledge_base USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- TABLE: channel_configs
-- Channel-specific configuration
-- ============================================================================
CREATE TABLE channel_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel VARCHAR(50) NOT NULL UNIQUE,
    config JSONB NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT channel_configs_channel_check CHECK (channel IN ('email', 'whatsapp', 'web_form'))
);

-- ============================================================================
-- TABLE: agent_metrics
-- Performance metrics and monitoring
-- ============================================================================
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_type VARCHAR(100) NOT NULL, -- 'message_processed', 'escalation', 'kb_search', etc.
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    channel VARCHAR(50),
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX idx_agent_metrics_type ON agent_metrics(metric_type);
CREATE INDEX idx_agent_metrics_name ON agent_metrics(metric_name);
CREATE INDEX idx_agent_metrics_timestamp ON agent_metrics(timestamp DESC);
CREATE INDEX idx_agent_metrics_channel ON agent_metrics(channel) WHERE channel IS NOT NULL;

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tickets_updated_at BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_base_updated_at BEFORE UPDATE ON knowledge_base
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_channel_configs_updated_at BEFORE UPDATE ON channel_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Active tickets with customer info
CREATE VIEW active_tickets_view AS
SELECT
    t.id,
    t.subject,
    t.status,
    t.priority,
    t.category,
    t.channel,
    t.created_at,
    c.email AS customer_email,
    c.name AS customer_name,
    c.phone AS customer_phone,
    (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = t.conversation_id) AS message_count
FROM tickets t
JOIN customers c ON t.customer_id = c.id
WHERE t.status IN ('open', 'in_progress');

-- View: Escalated tickets requiring human attention
CREATE VIEW escalated_tickets_view AS
SELECT
    t.id,
    t.subject,
    t.priority,
    t.category,
    t.channel,
    t.escalation_reason,
    t.escalated_at,
    t.assigned_to,
    c.email AS customer_email,
    c.name AS customer_name,
    c.phone AS customer_phone
FROM tickets t
JOIN customers c ON t.customer_id = c.id
WHERE t.status = 'escalated'
ORDER BY t.priority DESC, t.escalated_at ASC;

-- View: Channel performance metrics
CREATE VIEW channel_metrics_view AS
SELECT
    channel,
    COUNT(*) AS total_tickets,
    COUNT(*) FILTER (WHERE status = 'resolved') AS resolved_tickets,
    COUNT(*) FILTER (WHERE status = 'escalated') AS escalated_tickets,
    ROUND(AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/60), 2) AS avg_resolution_time_minutes
FROM tickets
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY channel;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert default channel configurations
INSERT INTO channel_configs (channel, config) VALUES
('email', '{
    "enabled": true,
    "max_response_length": 2000,
    "tone": "formal",
    "include_signature": true,
    "include_ticket_reference": true
}'::jsonb),
('whatsapp', '{
    "enabled": true,
    "max_response_length": 1600,
    "preferred_length": 300,
    "tone": "casual",
    "use_emojis": true,
    "max_emojis": 2
}'::jsonb),
('web_form', '{
    "enabled": true,
    "max_response_length": 1500,
    "tone": "semi-formal",
    "include_resources": true,
    "include_ticket_reference": true
}'::jsonb);

-- ============================================================================
-- GRANTS (adjust based on your user setup)
-- ============================================================================

-- Grant permissions to application user (replace 'app_user' with your actual user)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO app_user;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE customers IS 'Unified customer records across all communication channels';
COMMENT ON TABLE customer_identifiers IS 'Cross-channel customer identification with email/phone mapping';
COMMENT ON TABLE conversations IS 'Conversation threads tracking customer interactions';
COMMENT ON TABLE messages IS 'Individual messages within conversations';
COMMENT ON TABLE tickets IS 'Support tickets with status tracking and escalation';
COMMENT ON TABLE knowledge_base IS 'Product documentation with vector embeddings for semantic search';
COMMENT ON TABLE channel_configs IS 'Channel-specific configuration and settings';
COMMENT ON TABLE agent_metrics IS 'Performance metrics and monitoring data';

COMMENT ON COLUMN knowledge_base.embedding IS 'Vector embedding (1536 dimensions) from OpenAI text-embedding-3-small';
COMMENT ON COLUMN tickets.escalation_reason IS 'Reason for escalation: billing_issue, sales_opportunity, negative_sentiment, critical_issue, etc.';
