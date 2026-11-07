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
- **Scope note.** The privilege test excludes the implicit row type of a table or view: USAGE on it grants no data access, and the table itself is checked. Standalone types are checked.

## Phase 0 — Local token signing method (2026-11-07)

Observed against the local stack with a throwaway user (created via `POST /auth/v1/admin/users`, deleted afterwards):
- **User access tokens: `ES256`** (EC P-256), `kid` published at `GET /auth/v1/.well-known/jwks.json`. `iss` = `http://127.0.0.1:54321/auth/v1`, `aud` = `authenticated`.
- The legacy anon / service_role **API keys are HS256**. They are project keys, not user tokens; the backend must reject them as user credentials (Phase 1 test).
- Tokens carry a `role` claim; per invariant 22 it is ignored. Roles come from `app` tables.
- The cloud project's method is still to be reported by the owner (DECISIONS C4).
