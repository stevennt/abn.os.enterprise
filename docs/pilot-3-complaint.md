# Pilot 3: complaint auto-triage v1.0 (issue #94) — fast visible win for CS

AI triages (G65 contract live), humans send every reply. No auto-send, ever.

## Before/after metrics (4-week windows, same branches)

| Metric | Before (manual triage) | Target after | Abort if |
|---|---|---|---|
| triage p50 | 4h | ≤30 min | >2h for 3d |
| resolve p50 (S3) | 3d | ≤2d | worse than before 2 weeks |
| S1/S2 recall | manual (~0.97) | 1.00 | any miss |
| CSAT | baseline | ≥ baseline +0.2 | drops below baseline |
| agent min/complaint | 25 min | ≤15 min | no improvement in 2 weeks |

Method: same-branch before/after (no A/B on complaints — fairness), weekly readout
to CS leadership, dashboard panel H79. Kill: revert triage to manual queue in one
message; AI drafts stay as optional assistance.
