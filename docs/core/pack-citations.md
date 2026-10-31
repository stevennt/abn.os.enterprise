# Why the cross-repo cite checker was retired (issue #129)

## What it did

`abn.platform.opengate/qc/tools/check_enterprise_cites.py` verified that every
`abn.os.enterprise@<tag>` and `<RULE-ID>@<version>` written inside the banking pack
matched a pin file (`docs/enterprise-pins.yaml`).

## Why it was not enough

It compared **strings**. If the rule pack changed a threshold from 0.95 to 0.90 and
someone bumped the version string, the check stayed green while the skill's prose
kept quoting 0.95 to the model. The citation was *correct* and the *policy statement
was wrong* — the worst combination, because the audit trail looks clean.

It also depended on two repositories staying in step through a human ritual (bump
pin, remember to run the other repo's CI). Rituals are not guarantees.

## What replaced it

Co-location removed the failure mode instead of policing it. The pack now lives in
`industries/<id>/pack/`, next to `rules/`, `flows/`, `org/`. Three checks, in order
of increasing strength:

| Check | File | Catches |
|---|---|---|
| self-ref guard | `scripts/pack_lint.py` | pack citing an absolute external tag instead of a same-repo path |
| cite resolution | `scripts/pack_cite_check.py` | cited rule/flow/file is gone, or `@version` no longer matches the rule file |
| **numeric drift** | `scripts/pack_rule_drift.py` (issue #140, not yet written) | prose quotes a number that disagrees with the rule table — the class the old checker could never see |

The third check is the one that matters, and it is the reason this retirement is not
just bookkeeping: it parses thresholds out of pack prose and compares them with the
rule tables themselves. Co-location is what makes that possible at all; the old
machinery could not express it, because the two halves lived in different
repositories.

## What remains of pinning

A consumer (OpenGate) still pins *the bundle*, not individual rules:
`banking-pack-YYYY.MM.N` plus the tag's commit sha. That is a deployment concern, not
a policy concern, and it is recorded on the consumer side. This repo publishes the
two tag streams (`docs/core/release.md`) and verifies them
(`bin/verify-industry-tags.py`).

## Migration note for OpenGate

`qc/tools/check_enterprise_cites.py` and `docs/enterprise-pins.yaml` become dead
weight once the bundle path is live (L4-14/L4-15). Until then they still guard the
deprecated `domains/banking/` copy, which is frozen and must not be edited.
