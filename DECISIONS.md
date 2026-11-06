# Tollgate — Owner Decisions

Decisions on gaps in TOLLGATE_BUILD_SPEC.md, approved by the owner on 2026-11-07. One line each. Changing one needs owner approval; record the change here with a date.

## A — Money and currency
- **A1** Thresholds are explicit per currency in `rules.yaml` (`USD:` and `PKR:` blocks); no runtime FX conversion.
- **A2** All `*_cents` columns/fields mean integer minor units of the order's currency (PKR = paisa); names stay as in the spec.
- **A3** Rolling-window amount caps are computed per currency; rolling-window refund-count caps count across all currencies.
- **A4** Refund/store-credit currency is always the order's currency; a model-supplied currency is rejected as an unknown field.
- **A5** Thresholds are inclusive: `≤ auto_max` → ALLOW; `auto_max < x ≤ approval_max` → NEEDS_APPROVAL; `> approval_max` → DENY.
- **A6** Refunds and store credit share the rolling-window count and amount caps; store credit gets `approval_max_cents: 50000` (USD), DENY above.
- **A7** Rolling windows count `succeeded` + `pending_approval` refunds/credits; `rejected` and expired do not count.
- **A8** Amount columns stay `INT`; pydantic also bounds amounts to `0 < x ≤ 2^31-1`.

## B — Policy behaviour
- **B1** Add `order_items.downloaded_at TIMESTAMPTZ` to enforce `deny_digital_after_download`.
- **B2** Add `app.order_items` (order, product, quantity, unit price cents) in Phase 1.
- **B3** Refunds only on `delivered`/`partially_refunded` orders within the return window; `pending`/`paid` go via `cancel_order`; `packed`/`shipped` → DENY with an escalation hint.
- **B4** Refund amount = `min(DB item value, model amount_cents if given, refundable remainder)`.
- **B5** Above `approval_max` → DENY with reason `above_approval_max` + hint; the agent may call `create_ticket`; the gateway never opens tickets itself.
- **B6** On approve: re-check ownership, state, refundable remainder and every DENY rule on current data; NEEDS_APPROVAL counts as satisfied by the approval; the window excludes the request itself.
- **B7** Approval expiry (48h) is lazy: evaluated on read/act and on staff inbox load; no scheduler.
- **B8** Customer `tier` (`gold`) has no policy effect in v1.
- **B9** Frontend sends a `client_message_id` per chat message; backend dedupes on it so a double submit maps to one turn.

## C — Architecture
- **C1** BUFFER the final reply: SSE streams progress events live (status text, tool steps, action cards as soon as the gateway returns) plus a typing indicator; final reply text is released only after the claim check passes. Only checked text is ever sent or stored.
- **C2** Pending ActionCards poll their status (TanStack Query `refetchInterval`) while visible.
- **C3** `seed.sql` leaves `auth_user_id` NULL; `seed_store.py` creates the 3 demo users via the Auth admin API and links them. `--target cloud` is an explicit flag that shows the target project, requires typed confirmation, and refuses if store data exists unless `--reset` is also given. Tests never use it.
- **C4** JWT verification supports shared-secret and JWKS, selected per environment in config, with an explicit algorithm allowlist; never trust the token's `alg` header. Build against the local stack first; owner reports the cloud signing method later.
- **C5** Tests: per-test transaction rollback; concurrency/idempotency tests use separate connections with a full reseed.
- **C6** Two model slots in `.env`: `MODEL_FAST` and `MODEL_STRONG` (may hold the same ID).
- **C7** Frontend verification loop runs from Phase 0 (the Phase 0 gate requires a frontend build).
- **C8** Claim check is deterministic (action verbs + order IDs + amounts vs this turn's action log), tested with seeded false claims and benign negatives.
- **C9** Compose `api` reaches local Supabase via `host.docker.internal` (`extra_hosts`).

## D — Owner decisions
- **D1** Phase 5: multi-agent ships only if it beats single-agent by ≥ 3 of 40 scenarios on task success, cost per resolved scenario ≤ 1.3× single-agent, AND it does no worse on any must-deny or approval-required scenario.
- **D2** Hosting decided in Phase 7.
- **D3** Stay at $0; no paid LLM credit.
- **D4** PKR thresholds: auto ≤ Rs 15,000; approval ≤ Rs 150,000; 90-day auto cap Rs 30,000; stored in paisa. USD as in the spec.
- **D5** Gateway changes (Phase 5) only on a separate Gateway branch, following Gateway's CLAUDE.md and invariants, isolation suites re-run green, each change shown to the owner before committing. Owner creates the service-user credentials in `.env`; never ask for secrets in chat.
- **D6** `git init` at the start of Phase 0; local commits allowed at each passing gate with clear messages. Never push, never configure git credentials. Repo starts private; name/visibility decided before first push.
- **D7** Keep folder name `Customer_Support_Agent`; Python package is `tollgate`.
- **D8** LLM judge deferred to Phase 6+, run on the 12-scenario subset only.
- **D9** 12-scenario subset: 3 read-only, 2 auto-approved, 2 approval-required, 2 must-deny, 1 escalation, 2 ambiguous.
- **D10** Cap handoffs at 3 per turn, then escalate.
- **D11** PKR store-credit thresholds: auto ≤ Rs 30,000; approval ≤ Rs 150,000; DENY above. Stored in paisa. Store credit shares the rolling-window caps with refunds (A6).

## Tooling
- **T1** Verify external facts with WebFetch on official docs plus the installed source; Context7 not used for now.
