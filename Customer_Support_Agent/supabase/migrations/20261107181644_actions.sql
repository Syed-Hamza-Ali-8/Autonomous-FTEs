-- Phase 3 write actions (spec 6.2; DECISIONS H1, H2, I1-I8; backend/eval/ADVERSARIAL_PREREGISTRATION.md).
-- Same conventions as every app table: RLS on (no policies), row type revoked from PUBLIC.
-- Rows here are written only by the Action Gateway, its executors and the approval service.
-- Every created_at below is supplied by the caller from the injected clock (G1), so it has no default.

-- action_requests: one row per submission that had an EFFECT (executed or queued). Denials,
-- not-found and invalid submissions are only audited (app.audit_log), never recorded here.
CREATE SEQUENCE app.action_request_seq;
CREATE TABLE app.action_requests (
  id               text PRIMARY KEY
                   DEFAULT ('ACT-' || lpad(nextval('app.action_request_seq')::text, 6, '0'))
                   CHECK (id ~ '^ACT-[0-9]{4,}$'),
  customer_id      text NOT NULL REFERENCES app.customers (id),
  conversation_id  uuid REFERENCES app.conversations (id),
  turn_id          uuid NOT NULL,
  action           text NOT NULL CHECK (action IN ('request_refund', 'issue_store_credit', 'cancel_order',
                                                   'update_shipping_address', 'create_ticket',
                                                   'escalate_to_human')),
  order_id         text REFERENCES app.orders (id),
  order_item_ids   bigint[] NOT NULL DEFAULT '{}',  -- the lines a refund or credit covers (H1)
  amount_cents     integer CHECK (amount_cents > 0),  -- recomputed from the DB, never the model's
  currency         text CHECK (currency IN ('USD', 'PKR')),
  args             jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(args) = 'object'),
  decision         text NOT NULL CHECK (decision IN ('ALLOW', 'NEEDS_APPROVAL')),
  reasons          jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(reasons) = 'array'),
  status           text NOT NULL CHECK (status IN ('executed', 'pending_approval', 'approved', 'rejected',
                                                   'expired')),
  created_at       timestamptz NOT NULL,
  decided_at       timestamptz,
  CHECK ((decision = 'ALLOW') = (status = 'executed')),
  CHECK ((amount_cents IS NULL) = (currency IS NULL))
);
CREATE INDEX action_requests_order_idx ON app.action_requests (order_id, status);
CREATE INDEX action_requests_customer_idx ON app.action_requests (customer_id, created_at);
ALTER TABLE app.action_requests ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.action_requests FROM PUBLIC;

-- refunds (E1): action rows now reference their request, and get generated ids.
CREATE SEQUENCE app.refund_seq START 1001;
ALTER TABLE app.refunds
  ALTER COLUMN id SET DEFAULT ('REF-' || lpad(nextval('app.refund_seq')::text, 4, '0')),
  ADD CONSTRAINT refunds_action_request_fk FOREIGN KEY (action_request_id) REFERENCES app.action_requests (id);

-- store_credits: issued against an order's lines (I1); share the window and remainder rules with refunds.
CREATE SEQUENCE app.store_credit_seq;
CREATE TABLE app.store_credits (
  id                 text PRIMARY KEY
                     DEFAULT ('SC-' || lpad(nextval('app.store_credit_seq')::text, 4, '0'))
                     CHECK (id ~ '^SC-[0-9]{4,}$'),
  customer_id        text NOT NULL REFERENCES app.customers (id),
  order_id           text NOT NULL,
  currency           text NOT NULL,
  amount_cents       integer NOT NULL CHECK (amount_cents > 0),
  status             text NOT NULL CHECK (status IN ('pending_approval', 'succeeded', 'rejected')),
  action_request_id  text NOT NULL REFERENCES app.action_requests (id),
  reason             text,
  created_at         timestamptz NOT NULL,
  FOREIGN KEY (order_id, currency) REFERENCES app.orders (id, currency)
);
CREATE INDEX store_credits_customer_idx ON app.store_credits (customer_id, created_at);
CREATE INDEX store_credits_order_idx ON app.store_credits (order_id);
ALTER TABLE app.store_credits ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.store_credits FROM PUBLIC;

-- tickets: generated ids and a link to the request that opened them.
CREATE SEQUENCE app.ticket_seq;
ALTER TABLE app.tickets
  ALTER COLUMN id SET DEFAULT ('TKT-' || lpad(nextval('app.ticket_seq')::text, 4, '0')),
  ADD COLUMN action_request_id text REFERENCES app.action_requests (id);

-- idempotency_keys (I5): recorded only for an outcome with an effect, so action_request_id is required.
-- The primary key makes a concurrent duplicate fail instead of executing twice.
CREATE TABLE app.idempotency_keys (
  key                text PRIMARY KEY CHECK (key ~ '^[0-9a-f]{64}$'),
  customer_id        text NOT NULL REFERENCES app.customers (id),
  action_request_id  text NOT NULL REFERENCES app.action_requests (id),
  -- The original result as the exact JSON text returned, so a replay is byte-identical (jsonb would
  -- reorder its keys).
  result             text NOT NULL CHECK (jsonb_typeof(result::jsonb) = 'object'),
  created_at         timestamptz NOT NULL
);
ALTER TABLE app.idempotency_keys ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.idempotency_keys FROM PUBLIC;

-- audit_log: the gateway also records not-found, invalid and schema-rejected submissions, whose
-- decision is NULL (only ALLOW / NEEDS_APPROVAL / DENY are policy decisions).

-- Order status follows succeeded refunds (owner, DECISIONS I10): the refund executor sets it in the same
-- transaction as the refund. Checked at commit by a deferred constraint trigger, so a statement may
-- briefly disagree but no committed state can:
--   cancelled           -> succeeded refunds are 0 or exactly the captured total (H2 carries a full refund)
--   refunded            -> succeeded refunds equal the captured total (> 0)
--   partially_refunded  -> 0 < succeeded refunds < captured total
--   any other status    -> no succeeded refund
-- Pending refunds change nothing, and store credits are not refunds.
CREATE FUNCTION app.check_order_refund_status() RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $$
DECLARE
  -- One function for three tables: read the order id without naming a field the row may lack.
  oid       text := CASE TG_TABLE_NAME WHEN 'orders' THEN to_jsonb(NEW) ->> 'id' ELSE to_jsonb(NEW) ->> 'order_id' END;
  st        text;
  captured  bigint;
  refunded  bigint;
  ok        boolean;
BEGIN
  SELECT status INTO st FROM app.orders WHERE id = oid;
  SELECT coalesce(sum(amount_cents), 0) INTO captured FROM app.payments WHERE order_id = oid;
  SELECT coalesce(sum(amount_cents), 0) INTO refunded
    FROM app.refunds WHERE order_id = oid AND status = 'succeeded';
  ok := CASE st
          WHEN 'cancelled' THEN refunded = 0 OR refunded = captured
          WHEN 'refunded' THEN captured > 0 AND refunded = captured
          WHEN 'partially_refunded' THEN refunded > 0 AND refunded < captured
          ELSE refunded = 0
        END;
  IF NOT ok THEN
    RAISE EXCEPTION 'order % has status % but % of % captured refunded', oid, st, refunded, captured
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION app.check_order_refund_status() FROM PUBLIC;

CREATE CONSTRAINT TRIGGER refunds_order_status_consistent
  AFTER INSERT OR UPDATE ON app.refunds DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION app.check_order_refund_status();
CREATE CONSTRAINT TRIGGER orders_status_consistent
  AFTER INSERT OR UPDATE OF status ON app.orders DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION app.check_order_refund_status();
CREATE CONSTRAINT TRIGGER payments_order_status_consistent
  AFTER INSERT ON app.payments DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION app.check_order_refund_status();

-- No code path can create an already-decided request: a request is born executed or pending_approval,
-- and only the approval service (Phase 4) moves it on (invariant 7; af06 structural check).
CREATE FUNCTION app.reject_decided_action_request() RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
  IF NEW.status NOT IN ('executed', 'pending_approval') OR NEW.decided_at IS NOT NULL THEN
    RAISE EXCEPTION 'an action request must be created undecided' USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION app.reject_decided_action_request() FROM PUBLIC;

CREATE TRIGGER action_requests_born_undecided
  BEFORE INSERT ON app.action_requests
  FOR EACH ROW EXECUTE FUNCTION app.reject_decided_action_request();
