# Pilot 1: retail loan live v1.0 (issue #92) — the worked example in production

Requires Pilot 0 go-decision (J91). Runs the frozen loan flow (C22) under L3 guardrails.

## Pilot scope + caps

- 1 branch + mobile channel, daylight hours (08:00–17:00 ICT) only.
- Unsecured only, ≤300M VND (officer band, B11); manager approves EVERYTHING
  (no auto-approve path live, even for clean scores).
- Max 50 applications/day; overflow queues to next day (never to auto-approve).
- Kill conditions: any Sev1, default-signal anomaly, override rate >30%, CSAT <4.0.

## Daily review ritual (15 min, same faces)

- Yesterday: volumes, TTA, overrides with reasons, REVIEW queue aging, incidents.
- One decision: continue / tighten caps / pause. Pause needs no permission —
  any of branch_manager, credit_manager, risk_manager can halt intake in one message.
- Notes logged to the pilot log (feeds J100 scorecard + promotion evidence, A10).
