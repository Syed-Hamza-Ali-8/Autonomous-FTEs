-- The ActionCards of a turn, saved when the Action Gateway returns, not with the reply at the end of the turn
-- (owner, 2026-11-14). A turn that fails after the gateway acted (a rate limit, a provider error, a stop, a
-- crashed process) has no assistant message to carry its cards; without this the customer saw an error and an
-- empty chat although their refund was queued. Written in the same transaction as the action and its audit
-- row. Read only to show a finished turn that never replied; a replied turn's cards stay on its message.
CREATE TABLE app.turn_action_cards (
  id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  conversation_id  uuid NOT NULL REFERENCES app.conversations (id),
  turn_id          uuid NOT NULL,
  customer_id      text NOT NULL REFERENCES app.customers (id),
  card             jsonb NOT NULL CHECK (jsonb_typeof(card) = 'object'),
  created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX turn_action_cards_conversation_idx ON app.turn_action_cards (conversation_id, turn_id);
ALTER TABLE app.turn_action_cards ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.turn_action_cards FROM PUBLIC;
