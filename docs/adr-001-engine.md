# ADR-001: workflow engine choice (issue #51) — PROVISIONAL, confirmed or reversed by F52

Status: proposed (platform) — needs F52 hello-bank spike evidence to become accepted.
Context: flows are YAML-authored with analysts, rules are DMN packs, every decision
auditable; team runs Python/Axum/Frappe/Supabase; bank scale ~50M events/day.

## Comparison (scored for THIS program, not in general)

| Criterion | Camunda 8 | Temporal |
|---|---|---|
| Business readability (analyst owns flow) | BPMN native, Operate UI — strong | code-only — weak |
| DMN rules (E41–E45 packs) | native DMN engine — strong | sidecar needed — weak |
| Durable execution (retry/versioning) | good (Zeebe) | best in class |
| Dev ergonomics (Python team) | decent (py client) | excellent (SDK) |
| Ops burden | Zeebe cluster to run (or SaaS bill) | lighter self-host |
| Audit/visibility for regulators | Operate + history — strong | needs custom UI |
| License/cost | SaaS seats or self-manage effort | OSS, infra only |

## Decision

**Camunda 8 self-managed** as primary: this program's binding constraints are
analyst-owned BPMN + native DMN + regulator-visible history — exactly Camunda's
strengths, and exactly Temporal's gaps. Cost/ops risk is real, so: F52 builds the
loan flow on Camunda AND timeboxes a Temporal port; if Camunda ops prove heavier
than budgeted, this ADR reverses to Temporal with DMN sidecar (J99 prices both).

## Consequences

- F52 hello-bank runs on Camunda 8 (docker, 1 Zeebe gateway + Operate for stage).
- Flow YAMLs stay the source of truth; a BPMN exporter (track F) derives diagrams.
- J99 re-prices SaaS vs self-manage with real F52 numbers before scale-up.
