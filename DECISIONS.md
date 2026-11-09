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

## E — Phase 1 schema decisions (owner, 2026-11-07)
- **E1** `app.refunds` and the over-refund trigger move to Phase 1's store migration, with `source` (`historical` | `action`); `action_request_id` may be NULL only when `source='historical'` (CHECK). Phase 3 adds `action_requests` and the FK.
- **E2** Products are per-currency rows (regional SKUs). Composite FKs force order items and payments to match the order's currency in the DB. `order_items.unit_price_cents` is the price paid and the recompute source.
- **E3** Phase 1 seeds the two demo customers only; the support lead's Auth user and `staff_users` row are created together in Phase 4.

## F — Owner UI review, Phase 1 (2026-11-07)
- **F1** Money display: USD always shows cents; PKR drops ".00" when the paisa are zero. One formatter in `frontend/src/lib/format.ts` (unit-tested), mirrored by `backend/tollgate/domain/money.py` for the model's `display` strings.
- **F2** Dates display as "21 Aug 2026" in UTC on both sides; read tools return `<field>_display` so the model never formats dates.
- **F3** Order status pills are neutral; decision colours appear only as decision pills (refund status now, ActionCards from Phase 3). Only a success state may use a check icon.
- **F4** No floating chat launcher below 768px, and none on `/support` or order detail.
- **F5** Tests write through `tests/txpool.py` (rolled back); a row-count guard fails any pytest run that leaves rows behind. Live smoke and Playwright runs commit, because the token budget counts their `run_log` rows.
- **F6** Leak check (`backend/tests/leakcheck.py`): pytest and offline smoke allow no change. Real-model runs (live smoke, Playwright) may only grow `app.run_log`, `app.tool_calls`, `app.conversations`, `app.messages` (the real turn's trace; owner chose to keep it). Test logins use `tollgate-test+<purpose>-<hex>@example.test` and are purged at the start of every run.

## G — Phase 2 (owner, 2026-11-07)
- **G1** Decisions read time only from an injected `Clock` (`backend/tollgate/clock.py`). Fixture dates are offsets from a fixed `fixture_now` (2026-11-07T12:00:00Z) and `seed.sql` resolves them against it; tests and eval runs pin the clock there. The live demo uses the real clock (`seed_store.py apply --relative-dates`). Sanctioned wall-clock reads are listed with reasons in `tests/test_clock.py`.
- **G2** Evaluation anchors `ORD-1151`-`ORD-1158` (customers `CUS-041`-`CUS-044`) are appended to the fixture, labelled, with existing rows unchanged. They cover the 3rd-refund-in-90-days and split-refunds-cross-the-cap rules in USD and PKR. No application code may reference them (`tests/test_no_anchor_special_cases.py`); the Phase 3 model-free suite uses the same anchors.
- **G3** Read-only scenarios are scored by plain-text required facts plus forbidden facts (other customers' order IDs, tracking numbers, names); no LLM judge.

## H — Pre-registration approval (owner, 2026-11-07)
- **H1** No double compensation: a refund or credit for an order line that already has one pending or succeeded is DENY, and pending requests count against the order's refundable remainder. Switching a pending refund to store credit is therefore refused until staff decide.
- **H2** Cancelling a PAID order is one atomic action with its refund: exactly the captured total, recomputed from the DB, never partial, never model-supplied; auto-approved at any amount. Reasoning: nothing has shipped and the money returns to the original payment method, so there is no goods-for-money risk to gate. It does NOT count toward the 90-day cap, because that cap limits returns (goods kept, money back) and a pre-shipment cancellation is not a return. Above the refund approval max it is flagged in the audit for visibility, not gated.
- **H3** Suspected fraud: escalate, never cancel; the agent never makes a fraud determination.
- **H4** Token spend is mirrored to an append-only, git-ignored ledger (`.tollgate/token_spend.jsonl`); the pre-flight uses the higher of the ledger and `app.run_log`. Only real provider runs write to it (`LLMRuntime.ledger` is required; None for scripted models, tests and replays).
- **H5** Phase 3 targets: at least 22 of the 30 originally approved scenarios at the gate; stretch of at least 26 of 30 by Phase 6. The 5 scenarios added at approval (a09-a11, p09, p10) count toward every hard criterion and are reported separately.

## I — Phase 3 probe-set approval (owner, 2026-11-07; backend/eval/ADVERSARIAL_PREREGISTRATION.md)
- **I1** `issue_store_credit` takes `items` like `request_refund`, so H1 can tell which lines a credit covers.
- **I2** `items` is required for refunds and credits (amount-only is `INVALID items_required`). `amount_cents` stays optional as a ceiling alongside items, so a reduced goodwill refund on a line still works (B4). Shipping-only refunds are not supported in v1: the store charges no separate shipping (every order total equals its line sum), and the agent escalates such requests.
- **I3** Calls rejected by argument validation are audited from the tool's `failure_error_function` (and from the tool's own strict re-validation, because the SDK's argument model is lax). The audit row records that the call failed validation, the argument names and the validator's error locations and types; never argument values.
- **I4** Anchor `ORD-1161` / `CUS-047` (USD, delivered, 2 x 4K Monitor, $658) probes the USD approval-max boundary. Existing rows unchanged; G2 applies.
- **I5** Gateway order: validate -> ownership -> recompute -> idempotency -> policy -> route -> audit. Ownership precedes idempotency so an unauthorised request never reaches a key lookup. A key is recorded only for outcomes with an effect (executed or queued); a DENY records nothing and is re-evaluated on repeat.
- **I6** Concurrency probes run 20 iterations each in a scratch database cloned from the seeded one and dropped afterwards, behind the same localhost guard as the test suite (invariant 20).
- **I7** Reason codes as in the pre-registration, section 3. "Not yours" and "does not exist" share the single code `not_found` and produce byte-identical tool results.
- **I8** Paid-order cancel per H2, pinned by probes sv15, sv16, id04.
- **I9** af06 is narrowed, not renamed (amendment A1, 2026-11-08). The check is now structural: (a) no module a tool imports, directly or transitively, writes approval state; (b) no tool parameter maps to an approval column. The name heuristic stays as a secondary tripwire, with an explicit allowlist entry for `get_my_orders(status)`, an order-status filter on a read tool. A planted tool that accepts an approval status must fail the check (mutation M21). Phase 2 recordings stay valid.
- **I10** Order status follows succeeded refunds, set in the refund's own transaction. A full refund of the captured total sets `refunded`; a partial one sets `partially_refunded`. Pending refunds change nothing. A cancellation stays `cancelled` even though it carries a full refund. Store credit is not a refund. A deferred constraint trigger keeps every committed status consistent with the succeeded-refund sum. Knock-on: B3 now excludes a fully refunded order by its own status. This is a pre-code behaviour decision, not a loosened criterion: the changed probe expectations were re-derived by the independent verifier (pre-registration A1).
- **I11** (amends I6) Scratch databases are built from the same migrations and seed, with a one-table `auth.users` stand-in that keeps the FK shape, instead of being cloned from the live database. Before each concurrency run, the clone's `app` schema must be structurally identical to the main one (columns, types, constraints, triggers, indexes, sequences, functions, RLS); any difference aborts the run. The localhost-only guard is the same as the test suite's.

## Tooling
- **T1** Verify external facts with WebFetch on official docs plus the installed source; Context7 not used for now.
