# Tollgate — Evaluation Results

Every measured number in the README traces to an entry here and to a run file under `backend/eval/runs/`.
Failures and features turned off are recorded with the same prominence as gains (Rule 0.1.8).

## Phase 0 — Tool-calling probes (2026-11-07)

`backend/scripts/probe_tools.py`, provider Groq (`https://api.groq.com/openai/v1`), `openai-agents==0.24.0`.
Each model gets two probes. **raw** is one Chat Completions request with a `get_order_status` tool; it passes if exactly one function call arrives with `{"order_id": "ORD-1042"}`. **sdk** runs the same task through `Agent` + `OpenAIChatCompletionsModel` + `Runner.run`; it passes if the tool ran with `ORD-1042` and the final answer used the tool result.

Candidates were every general chat model on `GET /models`. Speech, TTS and prompt-guard/safeguard classifiers were excluded.

| Model | raw | sdk | Usable | Tokens (raw / sdk) | Latency ms (raw / sdk) | Run file |
|---|---|---|---|---|---|---|
| `openai/gpt-oss-20b` | pass | pass | **yes** | 219 / 486 | 615 / 857 | `probe_tools/20261107T122951Z.json` |
| `openai/gpt-oss-120b` | pass | pass | **yes** | 224 / 492 | 423 / 1025 | `probe_tools/20261107T122951Z.json` |
| `qwen/qwen3.8-27b` | pass | pass | **yes** | 365 / 808 | 536 / 429 | `probe_tools/20261107T122957Z.json` |
| `allam-2-7b` | **fail** | **fail** | **no** | — | — | `probe_tools/20261107T122957Z.json` |

- `allam-2-7b` failure: provider HTTP 400, "`tool calling` is not supported with this model". It is not used.
- Limits of this evidence: one sample per model on a single-tool, single-turn task. It shows tool calling *works*, not that it is reliable across multi-turn, multi-tool conversations. That is measured in Phase 2 onward.
- Groq's published limits for these three models (rate-limits page, 2026-11-07): 30 RPM, 1K RPD, 8K TPM, 200K TPD each. Per-model limits are separate; using two models in two slots is not multi-account rotation.

## Phase 0 — Supabase lockdown (2026-11-07)

Local stack: Supabase CLI 3.0.0, Postgres 17, PostgREST v16.5, gotrue v2.197.0. Migration `20261107124430_schema_and_lockdown.sql`.

`backend/tests/test_supabase_lockdown.py`: **7 passed**.

| Test | What it proves |
|---|---|
| `test_guard_accepts_only_local_urls` | The conftest guard accepts only localhost / 127.0.0.1 / ::1 (invariant 20) |
| `test_app_schema_not_in_exposed_schemas` | `app` is not in `[api].schemas` |
| `test_positive_control_anon_can_read_granted_public_table` | **Liveness:** the REST path, URL and anon key work (a granted public table is readable) |
| `test_anon_cannot_read_app_table_via_rest` | anon gets no data from `app` over REST, with or without `Accept-Profile: app` (observed: 406 `PGRST106`, 404 `PGRST205`) |
| `test_api_roles_have_no_privileges_in_app` | anon / authenticated have no privilege on the schema, tables, sequences, functions or standalone types in `app` |
| `test_privilege_check_is_not_vacuous` | **Liveness:** a probe table, sequence, function and enum exist in `app` during the run |
| `test_rls_enabled_on_every_app_table` | RLS is on for every `app` table, and at least one exists |

**Mutation check** (`scripts/mutation_lockdown.py`, run file `mutation/lockdown-20261107T125240Z.json`): baseline passed before and after; **4/4 mutations caught**.

| Mutation (protection removed) | Targeted test | Result |
|---|---|---|
| `grant_api_roles_on_app` (schema USAGE + default SELECT to anon/authenticated) | `test_api_roles_have_no_privileges_in_app` | failed as required |
| `public_execute_on_new_functions` (global default EXECUTE to PUBLIC restored) | `test_api_roles_have_no_privileges_in_app` | failed as required |
| `app_table_without_rls` | `test_rls_enabled_on_every_app_table` | failed as required |
| `expose_app_in_data_api` (`pgrst.db_schemas` includes `app`, plus grants) | `test_anon_cannot_read_app_table_via_rest` | failed as required |

Findings recorded honestly:
- **Gap found and fixed during Phase 0.** Postgres's built-in global defaults grant EXECUTE on new functions and USAGE on new types to PUBLIC, and the per-schema `REVOKE` could not remove them: a new `app` function was executable by anon. The migration now revokes both globally for objects created by `postgres`. The `public_execute_on_new_functions` mutation proves the test catches a regression.
- **Defence in depth, observed by hand.** With `app` exposed AND SELECT granted to anon, RLS with no policies still returned `200 []`. Only with RLS also disabled did the row leak. After revert: `406 PGRST106`.
- ~~**Scope note.** The privilege test excludes the implicit row type of a table or view: USAGE on it grants no data access, and the table itself is checked. Standalone types are checked.~~ Superseded below.

## Phase 0 — Local token signing method (2026-11-07)

Observed against the local stack with a throwaway user (created via `POST /auth/v1/admin/users`, deleted afterwards):
- **User access tokens: `ES256`** (EC P-256), `kid` published at `GET /auth/v1/.well-known/jwks.json`. `iss` = `http://127.0.0.1:54321/auth/v1`, `aud` = `authenticated`.
- The legacy anon / service_role **API keys are HS256**. They are project keys, not user tokens; the backend must reject them as user credentials (Phase 1 test).
- Tokens carry a `role` claim; per invariant 22 it is ignored. Roles come from `app` tables.
- The cloud project's method is still to be reported by the owner (DECISIONS C4).

### Update 2026-11-07: strict row-type handling (owner decision)

The row-type exclusion was removed from `test_api_roles_have_no_privileges_in_app`. Every table migration now revokes its implicit row type from PUBLIC (`REVOKE ALL ON TYPE app.<table> FROM PUBLIC;`), as the probe table does. Mutation re-run (`mutation/lockdown-20261107T131233Z.json`): baseline 7/7 before and after; **5/5 mutations caught**, including the new `app_table_row_type_not_revoked` (an RLS-enabled table without the row-type revoke), which fails `test_api_roles_have_no_privileges_in_app`.

## Phase 1 — Store, read tools, single agent, first UI (2026-11-07)

### Backend suites (local stack): 112 passed
| Suite | Tests | Mutation check |
|---|---|---|
| `test_supabase_lockdown.py` (now 11 real tables + probes) | 7 | 5/5 caught (Phase 0) |
| `test_store_schema.py`: refund trigger, split refunds, currency FKs, append-only payments, seed reproducibility | 12 | trigger behaviour tested directly |
| `test_auth_tokens.py`: expired, missing claims, wrong aud/iss, alg `none`, HS256 with public key / any secret / **anon key as secret**, RS256, kid/alg mismatch, foreign signing key, tampered payload, **anon and service-role keys as tokens**, real token accepted, JWKS outage fails closed | 33 | **8/8 caught** (`mutation/auth-20261107T132538Z.json`) |
| `test_read_isolation.py`: SQL owner filters; foreign / missing / malformed / lower-case IDs byte-identical; injected `customer_id` arg rejected; tool calls logged | 16 | **4/4 caught** (`mutation/reads-20261107T133057Z.json`) |
| `test_api.py`: identical 401 for 5 bad-token kinds on every route; 403 without customer row; two-customer isolation; identical 404s incl. headers; `no-store` + `Vary: Authorization`; chat buffering, claim check, B9 dedupe, conversation and order-context ownership, rate-limit and budget errors | 19 | covered by the unit mutations above |
| `test_claim_check.py` (v0) + `test_tool_registry.py` | 25 | Phase 6 adds the pre-registered claim suite and its mutation |

Note on `no_alg_allowlist`: with the allowlist removed, forged-alg tokens were still rejected by the second layer (kid -> algorithm binding); the mutation was caught because the tests assert the rejection reason.

### Two-customer isolation in the browser (owner gate item)
`frontend/tests/e2e/isolation.spec.ts`: **passed**. Customer A browses (list + order detail), signs out; customer B signs in **in the same tab** and browses. A MutationObserver recorded zero appearances of A's order IDs; no `sb-` session or order data left in browser storage after sign-out; B's deep link to A's order renders text identical to a nonexistent order.

Mutation check (`frontend/scripts/mutation-isolation.mjs`, `mutation/isolation-e2e-*.json`):
| Mutation | Result |
|---|---|
| user-scoped query keys AND cache clearing both removed (**required**) | **caught**: B was shown A's cached order list (B's own ORD-1046 never rendered) |
| cache clearing removed only (info) | not caught: user-scoped keys still isolate |
| user-scoped keys removed only (info) | not caught: clearing still isolates |
The two layers are independent; either alone holds, both removed leaks.

### Live gate conversation (`scripts/smoke.py --live`, model `openai/gpt-oss-120b`)
| Run | Result | Tokens / turn | Note |
|---|---|---|---|
| `smoke/phase1-20261107T134233Z.json` | **failed** 1 check | 2052 / 1599 / 1697 | Reply used U+2011 in `ORD‑1065`; plain substring check missed it. Investigating it exposed a **real claim-check bypass**: `I’ve refunded` (curly apostrophe) escaped the v0 pattern. Fixed by normalising typography before matching (tests added first, seen failing). |
| `smoke/phase1-20261107T134319Z.json` | **passed** all 10 checks | 2052 / 1600 / 1696 | Own order named; foreign ORD-1002 and nonexistent ORD-9999 both returned NOT_FOUND to the model and got word-for-word identical replies; no other-customer data; provider reported usage |
Criteria were not changed between runs.

### UI
- Phase 0 note closed: `--input` is zinc-500 in both themes (light 4.83 on white / 4.39 on muted; dark 4.12 / 3.67). The dark `white/15%` border (1.47) also failed and is fixed. Checked with `frontend/scripts/contrast.mjs`.
- Screenshots: `frontend/tests/e2e/__screenshots__/{desktop,mobile}-{light,dark}/` (41 files), every page asserted free of horizontal scroll. One real model turn spent for the conversation shots.
- Known, not yet fixed: replies show ISO dates (`2026-08-21`); a prompt change would be `support-v2` and belongs to Phase 2's measured prompt iteration.

## Phase 1 — Owner UI review round 1 (2026-11-07)

21 changes from the owner's review are implemented. Re-verified after all changes:
- Backend: **124 passed**; lint, strict types and offline smoke clean; fixture, seed.sql and openapi.json reproducible. Mutation checks re-run: lockdown **5/5**, auth **8/8**, reads **4/4** caught.
- Frontend: lint, typecheck and build clean; **12 unit tests** (`npm run test:unit`: formatter, status icons, chat suggestions). Browser isolation: passed; mutation re-run: required mutation **caught**, each single layer still isolates (info).
- Playwright: isolation + screenshots in 4 projects + a mobile keyboard check, all passing. 45 screenshots.

**Item 20, dates for the model (no prompt change).** Read tools now return a pre-formatted `<field>_display` date ("21 Aug 2026", UTC) next to every ISO timestamp, and PKR `display` money drops `.00` when the paisa are zero. Prompt `support-v1` is unchanged. Evidence: the real-model reply in the screenshot run reads "delivered on 21 Aug 2026" (before: "2026-08-21", Phase 1 smoke run files). One sample, not a measured rate; Phase 2 measures it.

**Item 21, test isolation (DECISIONS C5).** Root cause: the API tests, the read-tool tests and the offline smoke wrote through real connection pools (the app's and the tools'), so their conversations, messages, run_log, tool_calls and audit_log rows committed outside any test transaction. Fix: `tests/txpool.py` routes every pool query to one connection inside a rolled-back transaction, with a savepoint per test. The live smoke and the Playwright runs still commit on purpose: their `run_log` rows are what the rolling 24h token budget counts.
- Guard: `tests/conftest.py` counts rows in every `app` table and `auth.users` before and after each pytest run and fails the run on any difference. Shown live: before the fix it reported `app.conversations (0, 8), app.messages (0, 16), app.run_log (0, 8), app.tool_calls (0, 42), app.audit_log (0, 1)`; a deliberately leaking probe test made pytest exit 1.
- Proof on a fresh reset: all 15 tables had identical counts before and after `pytest` (112 tests at the time) plus the offline smoke.

**Item 19, overlap check.** At 390px, both the orders list and order detail are scrolled a screen at a time; no fixed or sticky element may intersect visible text. Shown live: putting the old floating launcher back on mobile made the check fail ("covers 'Clearance Hoodie and 1 more'").

Process note: one Playwright run was started with a stale spec (a Write was refused because the file had changed on disk). It was stopped before any model call. Its skipped teardown left two throwaway users linked; the teardown was run by hand and verified (0 linked, 0 Auth users).

## Phase 1 — Final fixes and GATE REPORT (2026-11-07)

### Final fixes (owner, after UI approval)
1. **Test logins.** Every test-created Auth user is `tollgate-test+<purpose>-<hex>@example.test` (`tests/auth_users.py`). pytest, the smoke runs and Playwright purge matching leftovers at the START of each run. Shown live: a planted leftover login linked to CUS-040 was removed before the next pytest run and its customer unlinked (0 links, 0 Auth users after). `auth.users` and the number of linked customers are part of the leak check.
2. **Leak check allowlist** (`tests/leakcheck.py`, DECISIONS F6). pytest and the offline smoke allow **no change at all**. Runs that call a real model (live smoke, Playwright) may only GROW `app.run_log` (token usage for the budget), `app.tool_calls`, `app.conversations` and `app.messages` (the real turn's trace), each with a comment; anything else, or any shrink, fails the run.
3. Sign-in panel and form card: equal height, top-aligned. 4. Mobile order detail order: Items, Refunds, Payment, Delivery (one grid; desktop placement unchanged). 5. Mobile filter chips: right-edge fade while more chips are hidden.

### Found while re-verifying (recorded, fixed)
- **Flaky auth mutation, fixed.** One `mutation_auth` run caught 7/8: with the audience check removed, `test_wrong_audience_is_rejected` still passed, because the token was rejected for a different reason and the test accepted any rejection. The likely cause is a backwards wall-clock step on WSL2 making the token's `iat` look in the future; that is a plausible explanation, not a reproduced one. Fix: every rejection test now asserts its specific reason (`InvalidAudienceError`, `InvalidIssuerError`, `MissingRequiredClaimError`, `InvalidSignatureError`, ...), and test tokens are issued 30s in the past. The tests got stricter, not looser; the verifier is unchanged. Then **8/8 on three consecutive runs**.
- **Fresh clone failed the frontend typecheck, fixed.** `LayoutProps` is generated by Next (`.next/`, `next-env.d.ts`, both git-ignored), so `tsc` failed on a clean checkout. Per the bundled Next docs, `npm run typecheck` is now `next typegen && tsc --noEmit`.

### Gate (spec Section 10, Phase 1 + owner items)
| Gate item | Status | Evidence |
|---|---|---|
| Fresh clone runs | **PASS** | Exactly the files git would commit (204), copied to an empty directory with only the owner's `.env` files added: `uv sync --frozen`, ruff, mypy, **124 tests**, smoke + leak check; `npm ci`, lint, typegen + typecheck, 12 unit tests, production build |
| Seed reproducible | **PASS** | `generate_fixture.py --check`, `seed_store.py write --check` (also a test) |
| Read tools filter by customer in SQL | **PASS** | `test_read_isolation.py`; mutation **4/4** caught |
| Smoke conversation: own order answered; foreign order refused indistinguishably from nonexistent | **PASS** | `smoke/phase1-20261107T163353Z.json` (current code): foreign ORD-1002 and nonexistent ORD-9999 both NOT_FOUND to the model, word-for-word identical replies; dates now "30 Oct 2026" |
| Screenshots of every page, 1440/390, light/dark, owner-reviewed | **PASS** | 45 files; owner approved the Phase 1 UI on 2026-11-07 |
| Owner: input border >= 3:1 | **PASS** | zinc-500: 4.83 / 4.39 light, 4.12 / 3.67 dark |
| Owner: two-customer isolation incl. TanStack cache after sign-out | **PASS** | `isolation.spec.ts`; required mutation caught; each layer alone isolates |
| Owner: anon-key, expired, forged-alg tokens rejected | **PASS** | `test_auth_tokens.py` + `test_api.py`; mutation **8/8** (x3) |
| Supabase lockdown still holds | **PASS** | 7/7; mutation **5/5** |
| Tests leave nothing behind | **PASS** | pytest leak check: 16 counts unchanged; Playwright and live smoke: only allowed tables grew |

**Known and accepted for Phase 1:** claim check is v0 (Phase 6 replaces it); "what was checked" status lines are shown live only (owner: staff see the tool trace in Phase 4); one live sample per change, not measured rates (Phase 2 measures).
