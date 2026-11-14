-- Audit trail and local tracing (spec Sections 1.2, 2.2, 6.2 step 7). SDK tracing to OpenAI is disabled;
-- every run and tool call is recorded here instead. All three tables are append-only.
-- Same conventions as every app table: RLS on (no policies), row type revoked from PUBLIC.

-- One row per agent turn.
CREATE TABLE app.run_log (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  turn_id          uuid NOT NULL UNIQUE,
  conversation_id  uuid NOT NULL REFERENCES app.conversations (id),
  customer_id      text NOT NULL REFERENCES app.customers (id),
  agent            text NOT NULL,
  prompt_version   text NOT NULL,
  model            text NOT NULL,
  status           text NOT NULL CHECK (status IN ('ok', 'error')),
  error            text,
  model_calls      integer NOT NULL DEFAULT 0 CHECK (model_calls >= 0),
  input_tokens     integer NOT NULL DEFAULT 0 CHECK (input_tokens >= 0),
  output_tokens    integer NOT NULL DEFAULT 0 CHECK (output_tokens >= 0),
  total_tokens     integer NOT NULL DEFAULT 0 CHECK (total_tokens >= 0),
  latency_ms       integer NOT NULL CHECK (latency_ms >= 0),
  started_at       timestamptz NOT NULL,
  finished_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX run_log_conversation_id_idx ON app.run_log (conversation_id, started_at);
CREATE INDEX run_log_model_started_idx ON app.run_log (model, started_at);  -- rolling 24h budget
ALTER TABLE app.run_log ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.run_log FROM PUBLIC;

-- One row per tool invocation inside a turn.
CREATE TABLE app.tool_calls (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  turn_id     uuid NOT NULL,
  tool_name   text NOT NULL,
  arguments   jsonb NOT NULL,
  outcome     text NOT NULL CHECK (outcome IN ('ok', 'not_found', 'error')),
  result      jsonb,
  latency_ms  integer NOT NULL CHECK (latency_ms >= 0),
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX tool_calls_turn_id_idx ON app.tool_calls (turn_id, id);
ALTER TABLE app.tool_calls ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.tool_calls FROM PUBLIC;

-- One row per Action Gateway submission, approval decision or other security-relevant event.
CREATE TABLE app.audit_log (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  at              timestamptz NOT NULL DEFAULT now(),
  actor_type      text NOT NULL CHECK (actor_type IN ('customer', 'staff', 'system')),
  actor_id        text NOT NULL,
  event           text NOT NULL,
  target          text,
  decision        text CHECK (decision IN ('ALLOW', 'NEEDS_APPROVAL', 'DENY')),
  reasons         jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(reasons) = 'array'),
  outcome         text,
  prompt_version  text,
  turn_id         uuid,
  details         jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(details) = 'object')
);
CREATE INDEX audit_log_at_idx ON app.audit_log (at DESC);
ALTER TABLE app.audit_log ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.audit_log FROM PUBLIC;

CREATE FUNCTION app.reject_log_change() RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
  RAISE EXCEPTION '% is append-only', TG_TABLE_NAME USING ERRCODE = 'restrict_violation';
END;
$$;
REVOKE ALL ON FUNCTION app.reject_log_change() FROM PUBLIC;

CREATE TRIGGER run_log_append_only BEFORE UPDATE OR DELETE ON app.run_log
  FOR EACH ROW EXECUTE FUNCTION app.reject_log_change();
CREATE TRIGGER tool_calls_append_only BEFORE UPDATE OR DELETE ON app.tool_calls
  FOR EACH ROW EXECUTE FUNCTION app.reject_log_change();
CREATE TRIGGER audit_log_append_only BEFORE UPDATE OR DELETE ON app.audit_log
  FOR EACH ROW EXECUTE FUNCTION app.reject_log_change();
