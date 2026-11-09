# Eval runs

| Run | What it is | Valid? |
|---|---|---|
| `20261107T173307Z` | Phase 2 read-only baseline (measured, 8/8). r07's original recording kept as `recordings/r07.contaminated.jsonl` (see its NOTE). | yes (measured scores) |
| `20261107T173639Z` | Clean re-recording of r07 only (PASS, 2,246 tokens) | yes |
| `replay-20261107T173307Z-20261107T173549Z` | First baseline replay, made with the buggy harness | **no**: see NOTE |
| `replay-20261107T173639Z-20261107T173646Z` | Replay of the r07 re-recording, made with the buggy harness | **no**: see NOTE |
| `replay-20261107T173307Z-20261107T173739Z` | Baseline replay after the fixes: all 8 faithful, 0 tokens | yes |

Recordings made before the sealing change have no integrity/input fingerprints and replay as
`unsealed_calls`; sealed recordings stop on any alteration or input drift.

## Tool-schema versions (CLAUDE.md: recordings are tied to a tool-schema version)
Every run above was recorded under prompt `support-v1` with read tools only. They predate the
`tool_schema_version` field, so their `meta.json` has none: they are **unversioned (before Phase 3)**.
Phase 3 gave the agent write tools and `support-v2` (tool schema `b8a139fe9dfd`). From then on, these recordings
are stale for replay: `run_eval.py --replay` refuses them unless `--allow-drift` is passed. They are kept as
the Phase 2 baseline record, and the affected scenarios are re-recorded under the new version.

| Run | What it is | Use its scores? |
|---|---|---|
| `20261107T213633Z` | Phase 3 batch 1 (14 write scenarios), tool schema `b8a139fe9dfd`: 12/14. p05 failed on a provider-side schema rejection caused by strict-mode tool schemas, fixed by `strict_mode=False` (schema `6fffe0b91095`). | As a measurement under `b8a139fe9dfd` only. **Stale for replay**: re-recorded under the new schema |
| `20261107T215559Z` | Phase 3, tool schema `6fffe0b91095` (current): p05 d01 d02 d03 e01, 5/5. To be resumed with the rest of the 30 originally approved scenarios. | yes |
