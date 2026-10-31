# Touchpoint analytics v1.0 (issue #79) — find where automation loses humans

## Event spec for analytics (emitted per touchpoint interaction, PII-free)

```
tp.view {journey, state, channel, instance_id}        # customer saw a state
tp.cta_click {journey, state, cta, instance_id}       # tapped e-sign/appeal/etc
tp.dropoff {journey, from_state, idle_seconds}        # left without progressing
tp.sla_breach {tp_id, over_by_minutes}               # any H71 breach
tp.csat {journey, score_1_5, instance_id}            # post-resolution rating
```

No PII in analytics events (ids are opaque; join to sealed data needs grant, D33).
Retention 1y aggregated, 90d raw. Funnel joins to instance KPIs via instance_id.

## Dashboard sketch (I82 panel "Journeys")

- Funnel per journey: view→click→complete with drop-off % between states;
  worst step highlighted with linked instances sample.
- TTA overlay (p50/p95 per journey) + SLA-breach heatmap by TP × hour.
- CSAT trend vs resolve time scatter; reopen-rate flag when a "resolved" journey
  re-enters within 7 days (failed resolution detector).
