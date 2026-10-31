# Pilot 0: eKYC sandbox cutover v1.0 (issue #91) — first live electrons

## Checklist

- [ ] Stage env matches F59 matrix; synthetic dataset loaded (D40 seed recorded).
- [ ] eKYC provider failover tested (primary → secondary → manual lane, H73/H80).
- [ ] PII handling sign-off by Data Protection (D33 tiers enforced, no prod PII in stage).
- [ ] Router + flow versions pinned (A04/A06); DLQ + alerts armed (H71).
- [ ] Branch drill done (H80 paper lane); CS briefed on status journey (H72).
- [ ] Rollback owner named; one-PR default flip tested in stage (A06).

## Rollback

Any Sev1, PII leak, or pass-rate <95% of baseline for 1h → flip to manual lane,
freeze the release tag, open incident. Rollback SLO 30 min, rehearsed pre-cutover.

## Success metrics (2-week window)

- pass_rate ≥  baseline −2pp, fraud_catch 100% on seeded cases, tta_p50 ≤ 3 min,
  review_rate stable, zero PII incidents, CSAT ≥ 4.5 on onboarded sample.
- Go/no-go to Pilot 1 (J92) needs all green + risk sign-off.
