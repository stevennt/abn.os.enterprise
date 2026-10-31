#!/usr/bin/env python3
"""Queue loop-5 prompts (issues 141-240) into the dashboard draft queue, top-first.

Each prompt is target-aware: it cds to the repo where the work belongs and uses
that repo's own verification commands, so Auto does not run bank-repo checks on
platform work (or vice versa).
"""
import json
import random
import string
import subprocess
import time
from pathlib import Path

REPO = "stevennt/abn.os.enterprise"
ENTERPRISE = "/Users/thanhson/Workspace/abn.os.enterprise"
OPENGATE = "/Users/thanhson/Workspace/abn.platform.opengate"
SESSION = "ses_e6fd7ed07ffe9bqG2jK5T6rfLH"
DRAFTS = Path("/Users/thanhson/.local/share/opencode/drafts.json")

ENT_VERIFY = ("yamllint the dirs you touched && python scripts/validate.py && every CI script in "
              ".github/workflows/validate.yml green (use &&, stop on red)")
OG_VERIFY = ("python3 gateway/resolve.py --root . --sync && validate-pack for each domain you touched && "
             "python3 -m pytest tests/ -q && npm run typecheck --prefix apps/api (and apps/web if touched)")

BG = {
 141: "schemas/customer.json, onboarding/tenant-template/, customers/hvcs/{profile,org}.json shapes",
 142: "schemas/sso.json (per-tenant OIDC, secret by env name), apps/api auth code, customers/*/profile.json",
 143: "schemas/sso.json, apps/api auth-user.ts, customers/README rules",
 144: "gateway/resolve.py (load_tenant_pins, --tenant), opengate.json customer key",
 145: "onboarding/tenant-template/{profile,org,instructions}.md",
 146: "customers/ layout, gateway/resolve.py path handling",
 147: "schemas/customer.json, customers/hvcs/profile.json",
 148: "schemas/org.json, customers/hvcs/org.json",
 149: "domains/base roles model, docs/roles.md maker/checker law, gateway/resolve.py role wiring",
 150: "customers/_platform/audit.jsonl, apps/api audit.service.ts",
 151: "schemas/org.json, customers/hvcs/org.json",
 152: "onboarding/industries.json, domains/*/roles.yaml",
 153: "schemas/org.json, docs/roles.md",
 154: "domains/legal/roles.yaml and domains/banking/roles.yaml patterns",
 155: "schemas/org.json, customers/hvcs/org.json",
 156: "schemas/org.json, infra/ scripts style",
 157: "gateway/resolve.py validate_org(), schemas/org.json",
 158: "schemas/org.json, apps/api roster code",
 159: "schemas/org.json, gateway/resolve.py version handling",
 160: "onboarding/industries.json, gateway/resolve.py domains",
 161: "customers/<t>/ layout, infra/files.py",
 162: "infra/files.py, infra/files/",
 163: "infra/files.py, apps/api file-scan.service.ts",
 164: "infra/files.py path handling",
 165: "infra/files.py, schemas/org.json units, apps/api",
 166: "infra/cases.py, customers/<t>/cases/<id>/case.json",
 167: "infra/files.py, onboarding/privacy.json",
 168: "infra/search.py, infra/search/",
 169: "infra/files.py, infra/cases.py",
 170: "infra/files.py, onboarding/plans.json",
 171: "domains/base (pack anatomy), domains/legal (biggest example), gateway/resolve.py validate_pack",
 172: "domains/legal/roles.yaml (authority pending-review pattern)",
 173: "domains/legal/skills/legal-citation, domains/base/skills",
 174: "domains/base/skills, domains/legal/templates",
 175: "onboarding/plans.json, gateway/resolve.py domains enable/disable",
 176: "gateway/bundle_store.py, customers/*/domains.json",
 177: "opengate.json domains, . /docs/domains.md",
 178: "docs/core/pack-mapping.md (here), gateway/bundle_store.py (there)",
 179: "gateway/resolve.py validate_pack, .github/workflows/gate.yml",
 180: "onboarding/industries.json, onboarding/plans.json",
 181: "gateway/resolve.py, apps/api auth, tests/",
 182: "apps/api auth-user.ts, schemas/sso.json",
 183: "schemas/sso.json (clientSecretEnv), vault rules",
 184: "schemas/customer.json, onboarding/privacy.json",
 185: "schemas/customer.json, apps/api analytics",
 186: "apps/api admin.controller.ts, roles",
 187: "apps/api audit.service.ts, customers/_platform/audit.jsonl",
 188: "apps/api, infra/",
 189: "infra/edge/pack.py (bundle pattern), customers/<t>/",
 190: "infra/files.py, infra/edge, customers/<t>/",
 191: "apps/web onboarding wizard, apps/api onboarding",
 192: "schemas/customer.json companies[], onboarding/tenant-template",
 193: "schemas/sso.json, apps/api auth.controller.ts",
 194: "onboarding/industries.json, onboarding/plans.json",
 195: "infra/files.py folder taxonomy",
 196: "infra/ scripts style, apps/api onboarding",
 197: "apps/api onboarding service, infra/",
 198: "apps/api onboarding, customers/<t>/",
 199: "tests/, onboarding/tenant-template",
 200: "apps/api controllers, bin/opengate CLI",
 201: "apps/web session/auth, apps/api auth-user.ts",
 202: "apps/web dashboard widgets",
 203: "apps/web, schemas/org.json",
 204: "apps/web, apps/api roster",
 205: "apps/web, infra/files.py",
 206: "infra/cases.py, apps/web cases.controller.ts",
 207: "apps/web admin console, apps/api admin.controller.ts",
 208: "schemas/sso.json, apps/api auth",
 209: "apps/web theme, customers/<t>/profile.json",
 210: "apps/web onboarding, gateway/resolve.py --sync output",
 211: "evals/, infra/finetune.py",
 212: "customers/<t>/models.json, infra/models.py",
 213: "infra/cases.py trace handling, onboarding/privacy.json",
 214: "apps/api analytics.service.ts",
 215: "onboarding/plans.json, apps/api analytics",
 216: "infra/files.py, infra/cases.py, schemas/org.json",
 217: "apps/api export, apps/web",
 218: "evals/, customers/<t>/",
 219: "apps/api analytics, evals/run.py",
 220: "apps/api, customers/<t>/",
 221: "onboarding/plans.json, gateway/resolve.py",
 222: "apps/api invite.service.ts, onboarding/plans.json",
 223: "apps/api analytics, onboarding/plans.json",
 224: "onboarding/plans.json, apps/api",
 225: "apps/api analytics.service.ts, onboarding/plans.json",
 226: "onboarding/privacy.json, schemas/customer.json",
 227: "onboarding/plans.json, gateway/resolve.py",
 228: "onboarding/plans.json",
 229: "apps/api analytics",
 230: "onboarding/tenant-template, customers/README",
 231: "this repo's bin/new-industry, docs/core/onboarding-industry.md",
 232: "docs/core/pack-mapping.md, docs/core/bundles.md (here); customers/<t>/domains.json (there)",
 233: "bin/tag-industry, bin/verify-industry-tags.py (here)",
 234: "everything above; customers/hvcs as the working example",
 235: "everything above plus schemas/org.json multi-company",
 236: "customers/ layout, gateway/resolve.py --sync",
 237: "schemas/sso.json, vault rules",
 238: "onboarding/, docs/",
 239: "onboarding/plans.json, customers/README",
 240: "all L5 issues",
}


def prompt(k, total, num, title, target):
    short = title.split("—", 1)[1].strip() if "—" in title else title
    if target == "opengate":
        where, verify = OPENGATE, OG_VERIFY
    elif target == "enterprise":
        where, verify = ENTERPRISE, ENT_VERIFY
    else:
        where = f"{ENTERPRISE} (contract/docs) then {OPENGATE} (implementation)"
        verify = f"enterprise checks in {ENTERPRISE}, then {OG_VERIFY} in {OPENGATE}"
    return (
      f"[L5-{k}/{total} · issue #{num}] {short}\n"
      f"Read first: gh issue view {num} --repo {REPO} --json title,body. "
      f"Target repo(s): {where}. Background: {BG.get(num, 'see the issue body')}.\n"
      f"Meet EVERY acceptance criterion. Keep uncommitted work from other sessions intact: stage only "
      f"this issue's files (never git add -A), branch DEV, git pull first.\n"
      f"Verify with && (stop on red): {verify}.\n"
      f"Then commit + push DEV ('Issue #{num}: ...') and close: gh issue close {num} --repo {REPO} "
      f"--comment 'Done: <files + proof + repo>'. Exactly this 1 issue. "
      f"If blocked, comment why on the issue and stop - do not guess."
    )


def main():
    raw = subprocess.run(["gh", "issue", "list", "--repo", REPO, "--state", "open",
                          "--label", "loop:5", "--limit", "150", "--json", "number,title,labels"],
                         capture_output=True, text=True, check=True).stdout
    issues = sorted(json.loads(raw), key=lambda x: x["number"])
    total = len(issues)
    prompts = []
    for k, it in enumerate(issues, 1):
        labels = {l["name"] for l in it.get("labels", [])}
        target = next((l.split(":", 1)[1] for l in labels if l.startswith("target:")), "opengate")
        prompts.append(prompt(k, total, it["number"], it["title"], target))
    out = Path(ENTERPRISE) / "docs" / "core" / "prompts" / "queue-loop5.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
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
    print(f"queued {len(new)} prompts; top = issue #{issues[0]['number']}; "
          f"stale tombstoned: {len(old)}; record: {out}")


if __name__ == "__main__":
    main()
