# Rollout wave 2 v1.0 (issue #96) — mortgage + cards, X-touchpoint maturity test

## Entry criteria (all from pilots 0–3, no exceptions)

- [ ] J91 green: eKYC pass ≈ baseline, fraud 100% seeded, zero PII incidents.
- [ ] J92 green: loan pilot TTA/override within caps, daily ritual stable 4 weeks.
- [ ] J93 green: transfer recon clean 30 days, zero double-posts.
- [ ] J94 green: triage targets met, CSAT not below baseline.
- [ ] J95 green: 3 branches live, mismatch <2%, no rollback in last 2 weeks.

## Wave scope

- Mortgage (C23): collateral leg with 2 appraiser firms + 1 notary panel per region;
  X-touchpoint docket staffed before first live case.
- Cards disputes (C27): scheme certification current, T-10d guardrail monitored daily.
- Caps start at 50% of BAU volume, step +25%/week on green metrics; any Sev1 reverts
  the wave to shadow mode (J95 re-entry rule).
