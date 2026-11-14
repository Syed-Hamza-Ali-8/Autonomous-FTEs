-- Support conversations, messages and tickets (spec Sections 3, 8; DECISIONS B9, C1).
-- Same conventions as every app table: RLS on (no policies), row type revoked from PUBLIC.
-- Ownership of a message is its conversation's customer_id; queries filter by it in SQL (invariant 3).

CREATE TABLE app.conversations (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id  text NOT NULL REFERENCES app.customers (id),
  order_id     text REFERENCES app.orders (id),  -- set when opened from "Get help with this order"
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX conversations_customer_id_idx ON app.conversations (customer_id, updated_at DESC);
ALTER TABLE app.conversations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.conversations FROM PUBLIC;

-- Only claim-checked assistant text is ever stored (C1). `system` rows are notifications
-- (e.g. approval outcomes, Phase 4) that the customer sees on their next visit.
CREATE TABLE app.messages (
  id                 bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  conversation_id    uuid NOT NULL REFERENCES app.conversations (id),
  turn_id            uuid NOT NULL,
  role               text NOT NULL CHECK (role IN ('customer', 'assistant', 'system')),
  content            text NOT NULL,
  client_message_id  uuid,  -- customer messages only; a repeated submit maps to one turn (B9)
  -- assistant messages: orders the customer's own tool results returned this turn, so inline order
  -- cards (13.3) survive a reload. Built from tool data, never parsed from the model's text.
  order_refs         text[] NOT NULL DEFAULT '{}',
  created_at         timestamptz NOT NULL DEFAULT now(),
  CHECK ((role = 'customer') = (client_message_id IS NOT NULL)),
  CHECK (role = 'assistant' OR order_refs = '{}'),
  UNIQUE (conversation_id, client_message_id)
);
CREATE INDEX messages_conversation_id_idx ON app.messages (conversation_id, id);
ALTER TABLE app.messages ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.messages FROM PUBLIC;

-- Written by the create_ticket / escalate_to_human tools through the Action Gateway (Phase 3+).
CREATE TABLE app.tickets (
  id               text PRIMARY KEY CHECK (id ~ '^TKT-[0-9]{4,}$'),
  customer_id      text NOT NULL REFERENCES app.customers (id),
  conversation_id  uuid REFERENCES app.conversations (id),
  kind             text NOT NULL CHECK (kind IN ('ticket', 'escalation')),
  category         text,
  summary          text NOT NULL,
  status           text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
  created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX tickets_customer_id_idx ON app.tickets (customer_id);
ALTER TABLE app.tickets ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.tickets FROM PUBLIC;
