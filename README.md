# Tollgate

An AI customer-support agent for the fictional store Northwind Goods. It resolves requests by taking real actions
(refunds, cancellations, address changes, store credit), and every risky action passes a checkpoint the model cannot
bypass: **the model proposes; deterministic code decides.**

*This README is a placeholder until the Phase 7 packaging; it starts with the measured limits that every reader of
the results needs.*

## Measured limits

### Reproducibility is bounded by the provider, not by our settings
In the Phase 4 evaluation run, 45 model calls returned **29 distinct `system_fingerprint` values** from the provider
(Groq, free tier). The requests were served by many different backend configurations, even within one run. So
**provider-side determinism is not available on this tier, whatever the temperature or seed**: temperature 0 with a
fixed seed doesn't make outputs repeatable across calls. Every result can still be re-scored exactly, because each run
records the model's outputs and replays them at zero tokens. Details are in `EVAL_RESULTS.md` (Phase 4).
