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
