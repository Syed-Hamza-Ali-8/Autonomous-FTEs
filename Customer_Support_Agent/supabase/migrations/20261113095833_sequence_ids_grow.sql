-- Sequence-backed ids grow past their padding instead of truncating (found 2026-11-13).
--
-- lpad() TRUNCATES a string longer than its target length: 'REF-' || lpad('10481', 4, '0') is 'REF-1048', so
-- sequence values 10480..10489 all produce the same id and every insert after the first collides on the
-- primary key. REF, SC and TKT (width 4) broke at 10,000; ACT and APR (width 6) would break at 1,000,000.
-- Every id CHECK already allows more digits ('^REF-[0-9]{4,}$'), so growing was always the intent.
-- Found when the local refund sequence (advanced by rolled-back tests; nextval is not transactional) passed 9999.
-- Existing ids are unchanged: every value below the width's limit renders exactly as before.

CREATE FUNCTION app.sequence_id(prefix text, n bigint, width integer) RETURNS text
LANGUAGE sql
IMMUTABLE
STRICT
SET search_path = ''
AS $$
  SELECT prefix || CASE WHEN length(n::text) >= width THEN n::text ELSE lpad(n::text, width, '0') END
$$;
REVOKE ALL ON FUNCTION app.sequence_id(text, bigint, integer) FROM PUBLIC;

ALTER TABLE app.refunds
  ALTER COLUMN id SET DEFAULT app.sequence_id('REF-', nextval('app.refund_seq'), 4);
ALTER TABLE app.store_credits
  ALTER COLUMN id SET DEFAULT app.sequence_id('SC-', nextval('app.store_credit_seq'), 4);
ALTER TABLE app.tickets
  ALTER COLUMN id SET DEFAULT app.sequence_id('TKT-', nextval('app.ticket_seq'), 4);
ALTER TABLE app.action_requests
  ALTER COLUMN id SET DEFAULT app.sequence_id('ACT-', nextval('app.action_request_seq'), 6);
ALTER TABLE app.approvals
  ALTER COLUMN id SET DEFAULT app.sequence_id('APR-', nextval('app.approval_seq'), 6);
