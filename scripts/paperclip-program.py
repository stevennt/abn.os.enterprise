#!/usr/bin/env python3
"""Paperclip program: 600 tasks, their GitHub issues, and the run queue.

The program is three tiers, each a set of workstreams, and each workstream is
decomposed by a ten-step ladder that fits its kind:

  design      draft → review → ratify → publish → enforce → test → cross-link
              → version → explain → audit
  build       spec → implement → wire → test → record → surface → document
              → harden → measure → demo
  ops         runbook → automate → alert → drill → measure → review → improve
              → document → train → audit
  compliance  map → implement → evidence → test → review → publish → train
              → audit → certify → renew

Tier 1 (100) builds the integration spine, tier 2 (200) the platform surface,
tier 3 (300) the industries, pilots and operations. Dependencies are linear
inside a workstream and chain across workstreams, so the catalog order *is* the
run order.

Usage:
  python3 scripts/paperclip-program.py catalog   # write the catalog JSON
  python3 scripts/paperclip-program.py create    # labels + 600 GitHub issues
  python3 scripts/paperclip-program.py queue     # prompts -> drafts store
  python3 scripts/paperclip-program.py status
"""
import json
import os
import random
import re
import string
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "docs" / "core" / "prompts" / "paperclip-catalog.json"
REPO = "stevennt/abn.os.enterprise"
DRAFTS = Path(os.path.expanduser("~/.local/share/opencode/drafts.json"))
SESSION_ENV = "OPENCODE_SESSION_ID"

ENTERPRISE = "/Users/thanhson/Workspace/abn.os.enterprise"
OPENGATE = "/Users/thanhson/Workspace/abn.platform.opengate"
ENT_VERIFY = ("python scripts/validate.py && python scripts/validate_company.py && "
              "python scripts/no_hardcoded_paths.py && python scripts/docs_link_check.py && "
              "python scripts/playbook_sync.py (use &&, stop on red)")
OG_VERIFY = ("python3 gateway/resolve.py --root . --sync && validate-pack for each domain you touched && "
             "python3 -m pytest tests/ -q && npm run typecheck --prefix apps/api (and apps/web if touched)")

KIND_STEPS = {
    "design": ["Draft", "Review", "Ratify", "Publish", "Enforce", "Test",
               "Cross-link", "Version", "Explain", "Audit"],
    "build": ["Spec", "Implement", "Wire", "Test", "Record", "Surface",
              "Document", "Harden", "Measure", "Demo"],
    "ops": ["Runbook", "Automate", "Alert", "Drill", "Measure", "Review",
            "Improve", "Document", "Train", "Audit"],
    "compliance": ["Map", "Implement", "Evidence", "Test", "Review", "Publish",
                   "Train", "Audit", "Certify", "Renew"],
}

STEP_CHECK = {
    "Draft": "the draft exists, names the decision and the alternatives, and is linked from the program doc",
    "Review": "the review comments are resolved or explicitly deferred with an owner",
    "Ratify": "the decision is recorded (ADR) and the program doc points at it",
    "Publish": "the artefact is reachable by the people who must follow it (path + link in the issue)",
    "Enforce": "a validator or test refuses the non-conforming case",
    "Test": "positive and negative cases run; a broken input is refused",
    "Cross-link": "the other repo/doc that must agree is linked both ways",
    "Version": "the artefact carries a version and the upgrade path is written",
    "Explain": "a newcomer can follow it without asking (checked by a fresh reader)",
    "Audit": "an operator can prove it from records, not memory (command + output)",
    "Spec": "the interface is written down (inputs, outputs, errors) before code",
    "Implement": "the code path exists and a test fails when the behaviour is removed",
    "Wire": "the real run path uses it (no parallel implementation) and the integration test covers it",
    "Record": "the record is written per run and validated by the repo's own sync/validators",
    "Surface": "a tenant admin or operator can see and act on it, permission-checked",
    "Document": "the doc has the exact commands and the expected output",
    "Harden": "failure modes are handled and the error names the fix",
    "Measure": "a metric/alert exists and it fired in a drill",
    "Demo": "one end-to-end run is recorded (command + output) and reproduces",
    "Runbook": "the runbook has trigger, steps, rollback and proof",
    "Automate": "the manual steps are a command/job with an idempotent re-run",
    "Alert": "the alert fires in a drill and names the first action",
    "Drill": "the drill ran, with timing and gaps recorded",
    "Improve": "the previous drill's gap is closed and re-measured",
    "Train": "the operator can run it from the doc alone (dry run recorded)",
    "Map": "every requirement is mapped to a control with an owner",
    "Evidence": "the evidence is collected automatically into the tenant record",
    "Certify": "the certification pack passes its own checklist",
    "Renew": "the renewal date and owner are recorded and alerted",
}

WORKSTREAMS = [
    # tier 1 — the integration spine (100)
    ("boundary", 1, "design", "enterprise", "Plane boundary: design vs control vs execution", "the three planes, what each owns, and the seam contracts"),
    ("compiler", 1, "build", "enterprise", "Compiler: Enterprise OS → Paperclip company template", "company.yaml + industry manifest into agents, projects, routines, skills"),
    ("adapter", 1, "build", "opengate", "Adapter: Paperclip task → OpenGate run", "heartbeat to run, context, artifacts, usage, errors"),
    ("identity", 1, "build", "both", "Identity: ONEID, tenant, people, agents", "org ↔ tenant, member ↔ account, agent service accounts"),
    ("policy", 1, "build", "opengate", "Policy: ACL and dataMode at the tool boundary", "resolve bundle, folder ACL, denied-action audit"),
    ("evidence", 1, "build", "opengate", "Evidence: activity → audit and metering", "Paperclip events into the tenant record"),
    ("money", 1, "build", "both", "Money: plan quota vs agent budgets", "seed budgets, ingest spend, reconcile"),
    ("governance", 1, "build", "both", "Governance: authority grid in approval gates", "maker/checker, escalation, audit"),
    ("portability", 1, "build", "enterprise", "Portability: company templates and contract pins", "export/import, pin, diff, rollback"),
    ("scaffolding", 1, "build", "both", "Program scaffolding: fixtures, CI, demo", "fake Paperclip, fake tenant, contract tests"),
    # tier 2 — the platform surface (200)
    ("connector-api", 2, "build", "opengate", "Connector API: tasks, runs, artifacts", "the HTTP/CLI surface between the two servers"),
    ("records", 2, "build", "opengate", "Records: cases, documents, work products", "Paperclip artifacts as tenant records with provenance"),
    ("tenant-onboarding", 2, "build", "both", "Tenant onboarding with a crew", "provision → crew template → first task"),
    ("admin-surface", 2, "build", "opengate", "Admin surface: the crew view", "who the agents are, what they may touch, what they spent"),
    ("readiness", 2, "build", "opengate", "Readiness and the go/no-go scorecard", "a crew as a gate item with evidence"),
    ("metering", 2, "build", "opengate", "Metering and statements for Paperclip work", "runs, artifacts, cost → tenant statement"),
    ("quotas", 2, "build", "opengate", "Quotas and rate limits at the edge", "per-tenant and per-agent limits"),
    ("secrets", 2, "build", "both", "Secrets: references, not values", "vault → run env, no copies in Paperclip"),
    ("residency", 2, "build", "opengate", "Residency and retention for agent output", "region tag, retention policy, purge"),
    ("pii", 2, "build", "opengate", "PII: classification and redaction in artifacts", "masking that keeps shape"),
    ("observability", 2, "ops", "opengate", "Observability: traces, logs, metrics", "one run visible end to end"),
    ("reliability", 2, "build", "opengate", "Reliability: retries, idempotency, DLQ", "no double work, no lost work"),
    ("security", 2, "build", "both", "Security: threat model to red team", "prompt injection, agent credentials, cross-tenant"),
    ("group-tenants", 2, "build", "opengate", "Group tenants: one crew per company", "company-scoped agents and evidence"),
    ("sync-semantics", 2, "design", "both", "Sync semantics: one-way, no dual writes", "who owns which field, and the watermark"),
    ("migration", 2, "build", "both", "Migration and backfill", "existing tenants into the new shape"),
    ("docs", 2, "ops", "both", "Docs and runbooks", "operator, admin, developer"),
    ("testing", 2, "build", "both", "Testing: unit, integration, e2e, chaos", "the pyramid for the boundary"),
    ("release", 2, "ops", "both", "Release engineering", "versioning, canary, rollback"),
    ("support", 2, "ops", "both", "Support and incident response", "Sev runbooks, comms, postmortem"),
    # tier 3 — industries, pilots, operations (300)
    ("banking", 3, "build", "enterprise", "Banking crew", "loan file work with sanctions and credit rules"),
    ("legal", 3, "build", "enterprise", "Legal crew", "charge review with citations and maker/checker"),
    ("medical", 3, "build", "enterprise", "Medical crew", "triage support with clinical guardrails"),
    ("civil-protection", 3, "build", "enterprise", "Civil protection crew", "incident response coordination"),
    ("defense-ops", 3, "build", "enterprise", "Defense operations crew", "readiness reporting with strict classification"),
    ("cross-industry", 3, "design", "enterprise", "Cross-industry patterns", "what every crew must share"),
    ("evals", 3, "build", "enterprise", "Evals and golden sets", "crew quality measured, not asserted"),
    ("quality", 3, "ops", "enterprise", "Quality metrics and reviews", "agent performance review from data"),
    ("training", 3, "ops", "enterprise", "Training and skill studio", "skills versioned, tested, restored"),
    ("pilot-wave-1", 3, "ops", "both", "Pilot wave 1", "one customer, one crew, go/no-go"),
    ("pilot-wave-2", 3, "ops", "both", "Pilot wave 2", "three customers, shared services"),
    ("pilot-wave-3", 3, "ops", "both", "Pilot wave 3", "a group tenant, two companies"),
    ("onboarding-playbook", 3, "ops", "both", "Customer onboarding playbook", "sales → crew → first value"),
    ("capacity", 3, "ops", "opengate", "Capacity planning", "agents × runs × tokens per host"),
    ("cost", 3, "ops", "both", "Cost optimization", "spend per outcome, not per token"),
    ("performance", 3, "ops", "opengate", "Performance", "p95 run latency and queue depth"),
    ("dr", 3, "ops", "opengate", "Disaster recovery and chaos", "restore a tenant and its crew"),
    ("multi-region", 3, "ops", "opengate", "Multi-region", "residency-aware placement"),
    ("gdpr", 3, "compliance", "both", "GDPR", "data-subject rights across both stores"),
    ("soc2", 3, "compliance", "both", "SOC 2", "controls with evidence"),
    ("sector-rules", 3, "compliance", "enterprise", "Sector rules", "banking, legal, medical obligations"),
    ("audit-cert", 3, "compliance", "both", "Audit and certification", "the pack an auditor accepts"),
    ("partners", 3, "build", "both", "Partner integrations", "connectors and resellers"),
    ("marketplace", 3, "build", "enterprise", "Crew marketplace", "publish and install crews"),
    ("analytics", 3, "build", "opengate", "Analytics and reporting", "work, cost, quality by tenant"),
    ("data-platform", 3, "build", "opengate", "Data platform", "events, warehouse, replay"),
    ("sre-runbooks", 3, "ops", "opengate", "SRE runbooks", "the on-call surface"),
    ("on-call", 3, "ops", "both", "On-call and incident drills", "rotations, pages, reviews"),
    ("roadmap", 3, "design", "enterprise", "Roadmap and governance", "what the next program is"),
    ("close-out", 3, "ops", "both", "Program close-out", "what shipped, what did not, next"),
]


TAGS = {
    "boundary": "plane contract", "compiler": "template mapping",
    "adapter": "run contract", "identity": "tenant identity",
    "policy": "ACL boundary", "evidence": "audit trail",
    "money": "budget reconciliation", "governance": "approval gates",
    "portability": "company templates", "scaffolding": "program harness",
    "connector-api": "task and run API", "records": "work products",
    "tenant-onboarding": "first crew", "admin-surface": "crew console",
    "readiness": "go/no-go input", "metering": "usage statement",
    "quotas": "edge limits", "secrets": "vault references",
    "residency": "region and retention", "pii": "artifact redaction",
    "observability": "run visibility", "reliability": "retry and DLQ",
    "security": "threat model", "group-tenants": "per-company crews",
    "sync-semantics": "field ownership", "migration": "tenant backfill",
    "docs": "operator docs", "testing": "test pyramid",
    "release": "canary and rollback", "support": "incident response",
    "banking": "loan crew", "legal": "charge review crew",
    "medical": "triage crew", "civil-protection": "incident crew",
    "defense-ops": "readiness crew", "cross-industry": "shared patterns",
    "evals": "golden sets", "quality": "agent reviews",
    "training": "skill studio", "pilot-wave-1": "one customer",
    "pilot-wave-2": "three customers", "pilot-wave-3": "group tenant",
    "onboarding-playbook": "sales to first value", "capacity": "host sizing",
    "cost": "cost per outcome", "performance": "run latency",
    "dr": "restore drill", "multi-region": "placement",
    "gdpr": "data-subject rights", "soc2": "controls and evidence",
    "sector-rules": "sector obligations", "audit-cert": "auditor pack",
    "partners": "connectors", "marketplace": "crew catalog",
    "analytics": "reporting", "data-platform": "events and replay",
    "sre-runbooks": "on-call surface", "on-call": "drills and reviews",
    "roadmap": "next program", "close-out": "program review",
}


def tasks():
    out = []
    previous = None
    for index, (key, tier, kind, target, name, scope) in enumerate(WORKSTREAMS, 1):
        steps = KIND_STEPS[kind]
        for step in steps:
            task_id = f"PC{tier}-{index:02d}-{steps.index(step) + 1:02d}"
            title = f"{name}: {step.lower()} — {TAGS[key]}"
            out.append({
                "id": task_id,
                "tier": tier,
                "workstream": key,
                "kind": kind,
                "target": target,
                "step": step,
                "title": title,
                "scope": scope,
                "depends_on": previous,
                "check": STEP_CHECK[step],
            })
            previous = task_id
    return out


def body(task, number=None):
    dep = (f"#{number_of[task['depends_on']]}" if task.get("depends_on")
           and task["depends_on"] in number_of else "—")
    where = (OPENGATE if task["target"] == "opengate" else
             ENTERPRISE if task["target"] == "enterprise" else
             f"{ENTERPRISE} (contract) then {OPENGATE} (implementation)")
    verify = OG_VERIFY if task["target"] == "opengate" else (
        ENT_VERIFY if task["target"] == "enterprise" else
        f"{ENT_VERIFY}, then {OG_VERIFY}")
    return f"""## Goal

{task['title']}

Part of the Paperclip program (tier {task['tier']}, workstream `{task['workstream']}`):
{task['scope']}.

## Scope

- step: **{task['step']}** — {task['check']}
- target repo(s): {where}
- depends on: {dep}

## Acceptance

- [ ] the artefact exists in the target repo and is committed on `DEV`
- [ ] {task['check']}
- [ ] one tenant/company demonstrates it end to end (command + output pasted in the issue)
- [ ] docs updated where the behaviour is user-visible
- [ ] other sessions' uncommitted work is untouched (stage only this issue's files)

## Verify

```bash
{verify}
```

## Definition of done

Commit + push `DEV` with `Issue #{number or '<n>'}: ...`, then close this issue with
`Done: <files + proof + repo>`. If blocked, comment why and stop — do not guess.
"""


number_of = {}


def catalog():
    data = {
        "version": 1,
        "program": "paperclip",
        "generatedAt": "2026-11-01",
        "tiers": {"1": 100, "2": 200, "3": 300},
        "tasks": tasks(),
    }
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print(f"catalog: {len(data['tasks'])} tasks -> {CATALOG}")


def labels():
    wanted = [
        ("loop:6", "Loop 6: Paperclip × OpenGate × Enterprise OS", "1a7f37"),
        ("tier:1", "Tier 1 — integration spine", "0e8a16"),
        ("tier:2", "Tier 2 — platform surface", "1d76db"),
        ("tier:3", "Tier 3 — industries, pilots, operations", "5319e7"),
        ("paperclip", "Paperclip program", "bfd4f2"),
        ("status:blocked", "Blocked — see the comment", "b60205"),
    ]
    have = json.loads(subprocess.run(
        ["gh", "label", "list", "--repo", REPO, "--limit", "200", "--json", "name"],
        capture_output=True, text=True, check=True).stdout)
    existing = {row["name"] for row in have}
    for name, description, color in wanted:
        if name in existing:
            continue
        subprocess.run(["gh", "label", "create", name, "--repo", REPO,
                        "--description", description, "--color", color],
                       capture_output=True, text=True)


def create():
    labels()
    data = json.loads(CATALOG.read_text()) if CATALOG.is_file() else None
    if data is None:
        catalog()
        data = json.loads(CATALOG.read_text())
    index = CATALOG.with_name("paperclip-issue-map.json")
    mapping = json.loads(index.read_text()) if index.is_file() else {}
    created = 0
    for task in data["tasks"]:
        if task["id"] in mapping:
            continue
        title = f"PC-{task['id']}: {task['title']}"
        path = Path(f"/tmp/pc-{task['id']}.md")
        path.write_text(body(task))
        number = None
        for attempt in range(40):
            result = subprocess.run(
                ["gh", "issue", "create", "--repo", REPO, "--title", title,
                 "--body-file", str(path), "--label", "loop:6", "--label", "paperclip",
                 "--label", f"tier:{task['tier']}", "--label", f"target:{task['target']}"],
                capture_output=True, text=True)
            out = (result.stdout or "").strip()
            if result.returncode == 0 and out.rsplit("/", 1)[-1].isdigit():
                number = int(out.rsplit("/", 1)[-1])
                break
            # gh can return 0 with an empty body when GitHub rejects the
            # mutation (issue-creation throttle): verify by looking for the title.
            latest = json.loads(subprocess.run(
                ["gh", "api", f"repos/{REPO}/issues?state=all&per_page=5",
                 "--jq", "[.[] | {number, title}]"], capture_output=True, text=True).stdout or "[]")
            match = next((row["number"] for row in latest if row["title"] == title), None)
            if match is not None:
                number = match
                break
            wait = 60 if attempt < 30 else 180
            print(f"throttled {task['id']} — wait {wait}s (attempt {attempt + 1})",
                  file=sys.stderr, flush=True)
            time.sleep(wait)
        if number is None:
            print(f"FAILED {task['id']} after retries", file=sys.stderr)
            continue
        mapping[task["id"]] = number
        number_of[task["id"]] = number
        index.write_text(json.dumps(mapping, indent=1))
        created += 1
        if created % 25 == 0:
            print(f"created {created} (last #{number})", flush=True)
        time.sleep(0.35)
    print(f"created {created}; mapped {len(mapping)}")


def queue():
    data = json.loads(CATALOG.read_text())
    index = CATALOG.with_name("paperclip-issue-map.json")
    mapping = json.loads(index.read_text())
    session = os.environ.get(SESSION_ENV, "ses_e6d244aa9ffeDU3doG1ZrSvcXq")
    tasks_by_id = {t["id"]: t for t in data["tasks"]}
    # catalog order is the dependency order (linear chain)
    prompts = []
    for order, task in enumerate(data["tasks"], 1):
        number = mapping.get(task["id"])
        if not number:
            continue
        where = ("abn.platform.opengate" if task["target"] == "opengate" else
                 "abn.os.enterprise" if task["target"] == "enterprise" else
                 "abn.os.enterprise then abn.platform.opengate")
        prompts.append({
            "order": order,
            "issue": number,
            "task": task["id"],
            "title": task["title"],
            "prompt": (
                f"[PC {order}/{len(data['tasks'])} · issue #{number}] {task['title']}\n"
                f"Read first: gh issue view {number} --repo {REPO} --json title,body. "
                f"Target repo(s): {where}. Step: {task['step']}.\n"
                f"Meet EVERY acceptance criterion. Keep uncommitted work from other sessions intact: "
                f"stage only this issue's files (never git add -A), branch DEV, git pull first.\n"
                f"Verify with && (stop on red): "
                + (OG_VERIFY if task["target"] == "opengate" else
                   ENT_VERIFY if task["target"] == "enterprise" else
                   f"enterprise checks, then {OG_VERIFY}")
                + f".\nThen commit + push DEV ('Issue #{number}: ...') and close: gh issue close {number} "
                  f"--repo {REPO} --comment 'Done: <files + proof + repo>'. Exactly this 1 issue. "
                  f"If blocked, comment why on the issue and stop - do not guess."
            ),
        })
    out = CATALOG.with_name("paperclip-queue.json")
    out.write_text(json.dumps(prompts, ensure_ascii=False, indent=1))

    store = json.loads(DRAFTS.read_text())
    entry = store.get(session, {"drafts": [], "sent": [], "deleted": {}})
    old = entry.get("drafts", [])
    base = max(int(time.time() * 1000),
               max([d.get("created", 0) for d in old] + [0])) + 1000
    rnd = lambda: "".join(random.choices(string.ascii_lowercase + string.digits, k=9))
    # newest `created` = top of the panel; first task must be on top
    new = [{"id": f"{base + (len(prompts) - p['order']) * 1000}-{rnd()}",
            "text": p["prompt"],
            "created": base + (len(prompts) - p["order"]) * 1000} for p in prompts]
    deleted = dict(entry.get("deleted", {}))
    for d in old:
        deleted[d["id"]] = base
    entry.update({"drafts": new, "sent": entry.get("sent", []),
                  "deleted": deleted, "updatedAt": base})
    store[session] = entry
    DRAFTS.write_text(json.dumps(store, ensure_ascii=False))
    print(f"queued {len(new)} prompts in {session}; top = #{prompts[0]['issue']} "
          f"({prompts[0]['task']}); last = #{prompts[-1]['issue']}")


def status():
    data = json.loads(CATALOG.read_text())
    index = CATALOG.with_name("paperclip-issue-map.json")
    mapping = json.loads(index.read_text()) if index.is_file() else {}
    print(f"tasks {len(data['tasks'])}, issues {len(mapping)}")
    for tier in (1, 2, 3):
        n = sum(1 for t in data["tasks"] if t["tier"] == tier)
        m = sum(1 for t in data["tasks"] if t["tier"] == tier and t["id"] in mapping)
        print(f"  tier {tier}: {m}/{n}")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "catalog"
    {"catalog": catalog, "create": create, "queue": queue,
     "status": status}.get(command, catalog)()
