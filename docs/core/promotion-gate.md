# L3 → L4 promotion gate v1.0 (issue #10)

No step runs fully auto (L4) on opinion. Promotion is a checklist with evidence;
anything missing = stay L3. The full pipeline implementation is I83; this doc
is the gate contract it enforces.

## Promotion checklist (all boxes, with evidence links)

- [ ] **Evals green:** golden suite for every AI step in the flow passes at the
  pinned model version (G67 harness). Eval report attached, no waivers.
- [ ] **30-day L3 audit window:** on live L3 traffic — error rate below the
  flow's threshold (default: wrong-decision <0.5%, override rate stable or
  falling), zero Sev1/Sev2, zero regulatory breaches. Window restarts on any breach.
- [ ] **Duplicate-injection green:** A07 suite passes on the frozen version.
- [ ] **Rollback plan:** one-rule-PR default flip (docs/core/versioning.md) tested in
  stage within the last 14 days; rollback owner named; rollback SLO ≤30 min.
- [ ] **Rule versions pinned:** every `uses_rule` cites an exact version; "latest" forbidden.
- [ ] **Touchpoints ready:** customer/employee comms for auto-decisions live (H72/H74),
  explainer template merged (I86).
- [ ] **Approvals:** flow owner + risk + compliance sign the promotion PR.
- [ ] **Monitoring:** KPI dashboard panel (I82) + `NO_ROUTE`/override alerts armed
  before cutover, not after.

## Demotion runbook (pointer)

Auto-demote to L3 on: any Sev1, any regulatory breach, eval regression on a
model bump, override-rate spike >2× baseline for 3 consecutive days.

Runbook steps live with ops (J98) and the pipeline (I83); the shape:

1. Flip default back to human-approve (same one-PR mechanism as rollback).
2. Freeze the L4 version tag; open an incident issue labeled `type:grc`.
3. Preserve audit chain + payload refs untouched for investigation.
4. Post-mortem within 5 business days; re-promotion needs a fresh 30-day window.

Demotion is never punished and never skipped: a demoted flow that "looks fine"
still serves L3 until the checklist above passes again in full.
