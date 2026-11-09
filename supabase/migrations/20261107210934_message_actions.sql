-- ActionCards on assistant messages (spec 13.3; DECISIONS C1): what the turn's write submissions did, as
-- the gateway reported it, stored with the claim-checked reply so the cards survive a reload. Built from
-- the gateway's outcomes, never from the model's text. Customer messages carry none.
ALTER TABLE app.messages
  ADD COLUMN actions jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(actions) = 'array'),
  ADD CONSTRAINT messages_actions_only_on_assistant CHECK (role = 'assistant' OR actions = '[]');
