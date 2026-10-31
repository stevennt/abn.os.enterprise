# 100%-automation scorecard v1.0 (issue #100) — closes the first loop, honestly

Filled quarterly from I82 metrics. v1 ships the template + the method; numbers arrive
with pilots (no invented figures — see G64 grounding discipline).

## Scorecard template (per industry, per process, per quarter)

Industries are scored separately first, then aggregated — a bank at 70% touchless and
a legal practice at 20% are not one number, and averaging them hides where the humans
actually are.

| Industry | Process | Touchless % | L4 steps % | Residual human-min/1k | TTA p50 | Override % | Quarter |
|---|---|---|---|---|---|---|---|
| `banking` | loan.retail.unsecured | _ | _ | _ | _ | _ | _ |
| `banking` | transfer.domestic | _ | _ | _ | _ | _ | _ |
| `legal` | legal.charge-review | _ | _ | _ | _ | _ | _ |
| **industry total** | `banking` | _ | _ | _ | — | _ | _ |
| **industry total** | `legal` | _ | _ | _ | — | _ | _ |
| **program total** | all industries | _ | _ | _ | — | _ | _ |

Per-industry rules: a `legal` process cannot be scored touchless while every rule row
still says `authority: pending-review` — an unreviewed pack is L2 at best, whatever the
step metadata claims.

Honesty rules: touchless counts instances with ZERO human touches (review lanes break
it); L4% counts steps, not flows; residual minutes measured, not estimated, from Q2.

## Top-10 residual-human causes (working list — re-ranked quarterly from data)

1. Regulatory sign-off required by law (STR filing, board approvals) — structural.
2. External X-touchpoint waits (notary, land office, appraisers).
3. Low-confidence AI abstains (tuned down via golden-set growth, G67).
4. Covenant waivers needing committee judgment (C24).
5. Complaint S1 empathy + remediation calls (C28).
6. Sanctions gray-zone reviews (E43 thresholds).
7. Valuation disputes (C23 re-appraisal loop).
8. New-product launches before rules stabilize (E50 intake lag).
9. Data-quality holds from producer outages (D38).
10. Customer-requested human handling (appeals, branch visits — keep this lane open).

## Next-12-month roadmap

- Q1: pilots 0–1 live (J91/J92), harness + drills green.
- Q2: pilots 2–3, wave-2 entry, measured-only costing begins (I90).
- Q3: waves 2–3 rollout, first L4 promotions through I83.
- Q4: J100 scored with real numbers; year-2 plan targets the top-3 causes above.
