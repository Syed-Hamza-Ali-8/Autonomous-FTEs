-- Phase 4 approvals (spec Section 8; DECISIONS B6, B7, E3, J7 / amendment A2-P4).
-- Same conventions as every app table: RLS on (no policies), row type revoked from PUBLIC.
--
-- Pending state lives on the request (action_requests.status = 'pending_approval'), set by the gateway's
-- queue. app.approvals is a decisions-only, append-only log written only by approvals/service.py. A request,
-- and its pending refund or credit, can only move on when a matching decision row exists, so a forger would
-- need two coordinated writes, one of them in the restricted module.

-- staff_users: who may decide (role from our tables, never from token claims, invariant 22) -----------------
CREATE TABLE app.staff_users (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_user_id  uuid UNIQUE REFERENCES auth.users (id) ON DELETE SET NULL,
  name          text NOT NULL,
  email         text NOT NULL UNIQUE CHECK (email = lower(email)),
  role          text NOT NULL CHECK (role = 'support_lead'),
  created_at    timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE app.staff_users ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.staff_users FROM PUBLIC;

-- approvals: one decision per request, never changed afterwards --------------------------------------------
CREATE SEQUENCE app.approval_seq;
CREATE TABLE app.approvals (
  id                 text PRIMARY KEY
                     DEFAULT ('APR-' || lpad(nextval('app.approval_seq')::text, 6, '0'))
                     CHECK (id ~ '^APR-[0-9]{4,}$'),
  action_request_id  text NOT NULL UNIQUE REFERENCES app.action_requests (id),
  decision           text NOT NULL CHECK (decision IN ('approved', 'rejected', 'expired', 'failed_recheck')),
  decided_by         uuid REFERENCES app.staff_users (id),
  note               text,
  recheck            jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(recheck) = 'object'),
  decided_at         timestamptz NOT NULL,
  -- expiry is the only decision nobody makes, and a rejection always says why
  CHECK ((decision = 'expired') = (decided_by IS NULL)),
  CHECK (decision <> 'rejected' OR length(btrim(coalesce(note, ''))) > 0)
);
ALTER TABLE app.approvals ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.approvals FROM PUBLIC;

CREATE TRIGGER approvals_append_only BEFORE UPDATE OR DELETE ON app.approvals
  FOR EACH ROW EXECUTE FUNCTION app.reject_log_change();

-- A decision can only be recorded for a request that is still waiting.
CREATE FUNCTION app.approval_needs_pending_request() RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $$
DECLARE
  st text;
BEGIN
  SELECT status INTO st FROM app.action_requests WHERE id = NEW.action_request_id;
  IF st IS DISTINCT FROM 'pending_approval' THEN
    RAISE EXCEPTION 'request % is not pending (status %)', NEW.action_request_id, st
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION app.approval_needs_pending_request() FROM PUBLIC;

CREATE TRIGGER approvals_need_pending_request BEFORE INSERT ON app.approvals
  FOR EACH ROW EXECUTE FUNCTION app.approval_needs_pending_request();

-- A request leaves pending_approval only with a matching decision; a decided request never changes again.
-- approved      needs decision 'approved'
-- rejected      needs decision 'rejected' or 'failed_recheck'
-- expired       needs decision 'expired'
-- executed      never from pending (an approval executes as 'approved')
CREATE FUNCTION app.action_request_decision_requires_approval() RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $$
DECLARE
  dec text;
  ok  boolean;
BEGIN
  IF NEW.status IS NOT DISTINCT FROM OLD.status THEN
    RETURN NEW;
  END IF;
  IF OLD.status <> 'pending_approval' THEN
    RAISE EXCEPTION 'request % is already %', OLD.id, OLD.status USING ERRCODE = 'check_violation';
  END IF;
  SELECT decision INTO dec FROM app.approvals WHERE action_request_id = OLD.id;
  ok := CASE NEW.status
          WHEN 'approved' THEN dec = 'approved'
          WHEN 'rejected' THEN dec IN ('rejected', 'failed_recheck')
          WHEN 'expired'  THEN dec = 'expired'
          ELSE false
        END;
  IF NOT coalesce(ok, false) THEN
    RAISE EXCEPTION 'request % cannot become % without a matching decision', OLD.id, NEW.status
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION app.action_request_decision_requires_approval() FROM PUBLIC;

CREATE TRIGGER action_requests_decision_requires_approval
  BEFORE UPDATE OF status ON app.action_requests
  FOR EACH ROW EXECUTE FUNCTION app.action_request_decision_requires_approval();

-- A pending refund or credit becomes succeeded only once its request is approved, and rejected only once its
-- request is rejected or expired (A2-P4 extension: a forger can't skip the request and move the money row).
CREATE FUNCTION app.money_row_follows_its_request() RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $$
DECLARE
  req text;
  ok  boolean;
BEGIN
  IF NEW.status IS NOT DISTINCT FROM OLD.status THEN
    RETURN NEW;
  END IF;
  IF OLD.status <> 'pending_approval' THEN
    RAISE EXCEPTION '% % is already %', TG_TABLE_NAME, OLD.id, OLD.status USING ERRCODE = 'check_violation';
  END IF;
  SELECT status INTO req FROM app.action_requests WHERE id = OLD.action_request_id;
  ok := CASE NEW.status
          WHEN 'succeeded' THEN req = 'approved'
          WHEN 'rejected'  THEN req IN ('rejected', 'expired')
          ELSE false
        END;
  IF NOT coalesce(ok, false) THEN
    RAISE EXCEPTION '% % cannot become % while its request is %', TG_TABLE_NAME, OLD.id, NEW.status, req
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION app.money_row_follows_its_request() FROM PUBLIC;

CREATE TRIGGER refunds_follow_their_request
  BEFORE UPDATE OF status ON app.refunds
  FOR EACH ROW WHEN (OLD.source = 'action')
  EXECUTE FUNCTION app.money_row_follows_its_request();
CREATE TRIGGER store_credits_follow_their_request
  BEFORE UPDATE OF status ON app.store_credits
  FOR EACH ROW EXECUTE FUNCTION app.money_row_follows_its_request();
