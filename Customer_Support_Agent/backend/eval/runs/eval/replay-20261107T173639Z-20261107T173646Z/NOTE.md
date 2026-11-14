# BUGGY HARNESS — kept as evidence (owner, Phase 2 gate)

Replay of the r07-only re-recording, made BEFORE the replay fixes. Its 7 "FAIL" rows (r01-r06, r08) are
NOT model or product failures: replay ran every phase<=2 scenario instead of only the recorded one, and
when those scenarios had no recording, the divergence was swallowed by the chat runner (which turns
unexpected errors into a friendly `server_error`). r07 itself replayed correctly (PASS, 2 calls).

What it shows: replay must select only recorded scenarios and must stop on divergence. Both fixed,
with regression tests.
