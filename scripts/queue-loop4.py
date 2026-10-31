#!/usr/bin/env python3
"""Queue loop-4 prompts (issues 123-140) into the dashboard draft queue, top-first."""
import json
import random
import string
import subprocess
import time
from pathlib import Path

REPO = "stevennt/abn.os.enterprise"
REPO_DIR = "/Users/thanhson/Workspace/abn.os.enterprise"
SESSION = "ses_e6fd7ed07ffe9bqG2jK5T6rfLH"
DRAFTS = Path("/Users/thanhson/.local/share/opencode/drafts.json")

BG = {
 123: "metamodel/org.schema.yaml (shape to copy), scripts/validate.py, docs/core-less repo layout in README.md",
 124: "current tree: rules/ events/ examples/bank/ ai/ evals/ templates/ + every script that references them",
 125: "docs/ (65 files), README.md repo map section, scripts/validate.py readme-map check",
 126: "docs/core/versioning.md (A06), existing tag banking-2026-10-31.1",
 127: "/Users/thanhson/Workspace/abn.platform.opengate/gateway/resolve.py (functions load_roles, skill_version, validate_pack) and domains/banking/{roles.yaml,skills/*/SKILL.md}",
 128: "/Users/thanhson/Workspace/abn.platform.opengate/domains/banking/ (read-only source), rules/aml-pack.yaml, rules/kyc-pack.yaml",
 129: "docs/enterprise-pins.yaml + qc/tools/check_enterprise_cites.py in abn.platform.opengate (read-only)",
 130: "Makefile-less repo; keep stdlib-only Python like other scripts",
 131: "industries/banking/ (after L4-02), /Users/thanhson/Workspace/abn.platform.opengate/domains/legal/ structure",
 132: "/Users/thanhson/Workspace/abn.platform.opengate/domains/legal/ (read-only), metamodel/pack.schema.yaml",
 133: "scripts/validate.py, all industries/*/industry.yaml",
 134: "docs/core/pii-policy.md (tier vocabulary to align), metamodel/org.schema.yaml",
 135: "scripts/validate.py, scripts/run_all_traces.py, scripts/export_bpmn.py, scripts/eval_harness.py, scripts/risk_pack.py, scripts/promo_pack.py, scripts/pii_scan.py",
 136: "/Users/thanhson/Workspace/abn.platform.opengate (target repo), docs/enterprise-pins.yaml here",
 137: "/Users/thanhson/Workspace/abn.platform.opengate (target repo), industries/banking/pack/ here",
 138: "docs/core/onboarding-industry.md, scripts/seed-loop4.py (issue bodies as checklist)",
 139: "README.md, ARCHITECTURE.md, ROADMAP.md, docs/core/scorecard.md, docs/core/cost-model.md, industries/banking/docs/cost-loan.md",
 140: "industries/banking/pack/skills/*/SKILL.md, industries/banking/rules/*.yaml",
}

def prompt(k, total, num, title, short):
    return (
      f"[L4-{k}/{total} · issue #{num}] {short} (repo abn.os.enterprise).\n"
      f"Work in {REPO_DIR}, branch DEV (git pull first).\n"
      f"1) Read: gh issue view {num} --repo {REPO} --json title,body. Meet EVERY acceptance criterion.\n"
      f"2) Background (read before editing): {BG.get(num, 'whole repo')}.\n"
      f"3) Keep all schemas/YAML valid; this repo is becoming multi-industry - shared vs per-industry split must hold.\n"
      f"4) Verify with && (stop on red): yamllint on dirs touched, python scripts/validate.py, and every CI script in .github/workflows/validate.yml.\n"
      f"5) Stage ONLY this issue's files (never git add -A - other work may be uncommitted); commit + push DEV ('Issue #{num}: ...'), then close: gh issue close {num} --repo {REPO} --comment 'Done: <files + proof>'.\n"
      f"Exactly this 1 issue. Blocked? comment why on the issue and stop, no guessing."
    )

def main():
    raw = subprocess.run(["gh", "issue", "list", "--repo", REPO, "--state", "open",
                          "--label", "loop:4", "--limit", "40", "--json", "number,title"],
                         capture_output=True, text=True, check=True).stdout
    issues = sorted(json.loads(raw), key=lambda x: x["number"])
    total = len(issues)
    prompts = []
    for k, it in enumerate(issues, 1):
        short = it["title"].split("—", 1)[1].strip() if "—" in it["title"] else it["title"]
        prompts.append(prompt(k, total, it["number"], it["title"], short))
    (Path(REPO_DIR) / "docs" / "core" / "prompts" / "queue-loop4.json").write_text(json.dumps(
        [{"order": k, "issue": it["number"], "title": it["title"], "prompt": p}
         for k, (it, p) in enumerate(zip(issues, prompts), 1)], ensure_ascii=False, indent=1))
    store = json.loads(DRAFTS.read_text())
    entry = store.get(SESSION, {"drafts": [], "sent": [], "deleted": {}})
    old = entry.get("drafts", [])
    base = max(int(time.time() * 1000), max([d.get("created", 0) for d in old] + [0])) + 1000
    rnd = lambda: "".join(random.choices(string.ascii_lowercase + string.digits, k=9))
    new = [{"id": f"{base + (total - k) * 1000}-{rnd()}", "text": p,
            "created": base + (total - k) * 1000} for k, p in enumerate(prompts, 1)]
    deleted = dict(entry.get("deleted", {}))
    for d in old:
        deleted[d["id"]] = base
    entry.update({"drafts": new, "sent": entry.get("sent", []),
                  "deleted": deleted, "updatedAt": base})
    store[SESSION] = entry
    DRAFTS.write_text(json.dumps(store, ensure_ascii=False))
    print(f"queued {len(new)} prompts (top: issue #{issues[0]['number']}), stale tombstoned: {len(old)}")

if __name__ == "__main__":
    main()
