# Promotion pipeline v1.0 (issue #83) — boring and safe, gate contract in A10

## Pipeline stages (`promo check|promote|demote <flow> <version>`)

1. **Collect:** evidence-pack builder pulls eval report (G67), 30d audit window
   metrics (I82), injection suite result (A07), load-test report (F60), cost sheet
   (G69/I90) into one signed pack.
2. **Gate-check:** every A10 box verified programmatically; missing box = stop with
   named gap (no partial promotions, no waivers).
3. **Sign:** flow owner + risk + compliance e-sign the pack (F57); signatures in audit.
4. **Cutover:** default version flips per A06 dual-run; L4 badge on dashboard.
5. **Watch:** 14-day heightened monitoring (alerts at 50% of demote thresholds).

## Demote runbook (auto + manual)

Auto-demote webhook fires on: Sev1, regulatory breach, eval regression on model bump,
REVIEW rate >2× baseline 3d, cost >150% budget. Webhook flips default to L3 in <5 min,
freezes the L4 tag, opens a `type:grc` incident with the evidence snapshot.
Manual demote: one command, same path, any of the 3 signers. Re-promotion needs a
fresh 30-day window (A10) — no shortcuts, no matter how good it looks.
