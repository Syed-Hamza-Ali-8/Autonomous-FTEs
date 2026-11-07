# Recording note (2026-11-07)

`r07.contaminated.jsonl` is the original r07 recording. It holds 3 calls: the first is a stale call
from an attempt that was rate-limited mid-turn and retried. Recording at that time appended every
completed call, including calls from failed attempts. The bug is fixed: recordings are buffered per
attempt and only successful attempts are written (`eval/models.py`, test
`test_rate_limited_attempt_is_not_recorded`).

`r07.jsonl` is a clean re-recording of the same scenario, from run `20261107T173639Z`, with the same
model and prompt (support-v1). Its score (PASS) matches this run's measured result. The scores in
`results.jsonl` are this run's original measurements and were not edited.
