# BUGGY HARNESS — kept as evidence (owner, Phase 2 gate)

First replay of the baseline, made BEFORE the recording fix. It reported 8/8 "faithful", but r07 was not:
r07's recording contained a stale call from a rate-limited attempt, so this replay made two `get_order`
calls where the real successful turn made one. It matched the measured row only by coincidence, because
that row also counted the failed attempt (3 calls, 3,026 tokens).

What it shows: a replay can look faithful while not being faithful. Fixes: recordings buffered per
attempt (only successful attempts written), sealed recordings with integrity + input fingerprints,
divergence stops the run. Valid replay: `replay-20261107T173307Z-20261107T173739Z`.
