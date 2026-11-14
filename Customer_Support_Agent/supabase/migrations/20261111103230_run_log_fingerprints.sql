-- Phase 4 run set-up (pre-registration 12.4; DECISIONS J4, J14): the provider's system_fingerprint for every
-- model call in a turn, so the repeatability figure can show whether the serving backend changed between runs.
ALTER TABLE app.run_log ADD COLUMN system_fingerprints text[] NOT NULL DEFAULT '{}';
