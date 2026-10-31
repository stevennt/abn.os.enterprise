# Fraud/AML drill scenarios v1.0 (issue #84) — prove the OS under attack

Quarterly game-day in stage (F59) with synthetic actors (D40). Each card states the
attack, the injection, and the expected hold. A missed hold = Sev1 + track-G eval gap.

## Scenario cards (10)

| # | Attack | Injection | Expected hold |
|---|---|---|---|
| 1 | mule ring (fan-in) | 20 accounts → 1 beneficiary, 2h | velocity hold + STR triage |
| 2 | structuring | 9× just-under-threshold cash deposits | aggregation hold (C25) |
| 3 | forged payslip | font mismatch + round income | s2 abstain → REVIEW (G62) |
| 4 | synthetic identity | valid CCCD + new phone + thin file | KYC REVIEW, no auto-pass |
| 5 | account takeover | new device + password reset + transfer | step-up verify, transfer held |
| 6 | invoice fraud (BEC) | vendor bank change via email | callback verify, payment held |
| 7 | sanctions evasion (alias) | fuzzy-name near listed entity | screening REVIEW ≥0.80 (E43) |
| 8 | belső collusion | officer approves own referral | SoD deny at claim (B19) |
| 9 | loan stacking | 3 concurrent apps across channels | velocity hold, joint review |
| 10 | complaint social-engineering | "urgent refund" call + fake receipt | call-verify flow, no refund without case |

Pass = 10/10 expected holds + evidence packs complete (C25) + zero customer-PII
in drill artifacts (D33). Failures feed G67 golden sets within 14 days.
