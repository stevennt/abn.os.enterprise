#!/usr/bin/env python3
"""Audit the plane boundary from records, not memory (ADR-002, issue #251).

An audit is not a feeling that the checks pass. This runs the boundary's own
checks, records each command, its exit code, the digest of what it printed and
the digest of the files it guards, and writes a report that can be handed to
somebody else and re-verified later.

  python scripts/audit_boundary.py --out docs/core/audits/plane-boundary-<date>.json
  python scripts/audit_boundary.py --verify docs/core/audits/plane-boundary-<date>.json

`--verify` re-runs every check and fails when an exit code differs or the
contract version moved. It warns (does not fail) when the guarded files changed
after the report — that is what editing a document does, and the report says
which digests it saw.

The report carries `paperclip-boundary@<version>` from the contract, the commit
it ran at, the open items inherited by the tiers (with their issues) and a
verdict. It is the evidence the "audit" step of the boundary workstream means.
"""
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "docs" / "core" / "paperclip-integration.md"
VERSION = re.compile(r"paperclip-boundary@\d+\.\d+")
CHECKS = (
    ("boundary", ["scripts/check_plane_boundary.py"]),
    ("boundary self-test", ["scripts/check_plane_boundary.py", "--self-test"]),
    ("contract tests", ["scripts/test_plane_contract.py"]),
    ("contract self-test", ["scripts/test_plane_contract.py", "--self-test"]),
    ("template spec", ["scripts/check_paperclip_template.py", "--template",
                       "tests/fixtures/paperclip-company.example.json"]),
    ("template self-test", ["scripts/check_paperclip_template.py", "--self-test"]),
    ("compiler", ["scripts/test_paperclip_company.py"]),
    ("compiler self-test", ["bin/paperclip-company", "--self-test"]),
    ("compiler --all", ["bin/paperclip-company", "--all", "--check"]),
    ("compiler metrics", ["bin/paperclip-company", "--metrics", "--fail-on-alert"]),
    ("compiler drill", ["bin/paperclip-company", "--drill"]),
    ("compile records", ["scripts/validate_compiles.py", "--root",
                         "tests/fixtures/paperclip-model"]),
    ("compile records self-test", ["scripts/validate_compiles.py", "--self-test"]),
    ("docs links", ["scripts/docs_link_check.py"]),
    ("playbook", ["scripts/playbook_sync.py"]),
    ("industry model", ["scripts/validate.py"]),
    ("company model", ["scripts/validate_company.py"]),
)
GUARDED = (
    "docs/core/paperclip-integration.md",
    "docs/core/adr-002-paperclip-three-planes.md",
    "docs/core/paperclip-reviews/PC1-01-02-plane-contract.md",
    "docs/core/paperclip-explainer.md",
    "docs/core/paperclip-reviews/PC1-01-09-explainer.md",
    "scripts/check_plane_boundary.py",
    "scripts/test_plane_contract.py",
    "scripts/check_paperclip_template.py",
    "scripts/test_paperclip_company.py",
    "scripts/validate_compiles.py",
    "bin/paperclip-company",
    "schemas/paperclip-company.json",
    "tests/fixtures/paperclip-company.example.json",
    "docs/core/paperclip-compiler.md",
    "scripts/audit_boundary.py",
)
OPEN_ITEMS = (
    {"item": "run-context mode in resolve.py", "issue": 283},
    {"item": "agent service accounts (no password)", "issue": 273},
    {"item": "per-agent budget vs tenant ceiling, group split", "issue": 302},
    {"item": "OpenGate-down semantics (fail closed)", "issue": 352},
)


def _sha(path):
    data = (ROOT / path).read_bytes() if (ROOT / path).is_file() else b""
    return hashlib.sha256(data).hexdigest() if data else None


def _commit():
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True)
        return out.stdout.strip() or None if out.returncode == 0 else None
    except OSError:
        return None


def _run(check):
    name, args = check
    result = subprocess.run([sys.executable, *args], cwd=ROOT,
                            capture_output=True, text=True)
    output = (result.stdout or "") + (result.stderr or "")
    lines = [line for line in output.strip().splitlines() if line.strip()]
    return {
        "check": name,
        "command": " ".join(["python", *args]),
        "exit": result.returncode,
        "outputSha256": hashlib.sha256(output.encode()).hexdigest(),
        "summary": lines[-1] if lines else "",
    }


def audit():
    version = VERSION.search(CONTRACT.read_text() if CONTRACT.is_file() else "")
    checks = [_run(check) for check in CHECKS]
    return {
        "version": 1,
        "kind": "plane-boundary-audit",
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit": _commit(),
        "contract": version.group(0) if version else None,
        "checks": checks,
        "inputs": {path: _sha(path) for path in GUARDED},
        "openItems": list(OPEN_ITEMS),
        "verdict": "pass" if all(row["exit"] == 0 for row in checks) else "fail",
    }


def _markdown(report):
    lines = [
        "# Plane boundary audit",
        "",
        f"- contract: `{report['contract']}`",
        f"- commit: `{report['commit']}`",
        f"- at: {report['at']}",
        f"- **verdict: {report['verdict'].upper()}**",
        "",
        "| Check | Exit | What it said |",
        "|---|---|---|",
    ]
    for row in report["checks"]:
        lines.append(f"| {row['check']} | {row['exit']} | {row['summary']} |")
    lines += ["", "## Open items inherited by the tiers", "",
              "| Item | Issue |", "|---|---|"]
    for item in report["openItems"]:
        lines.append(f"| {item['item']} | #{item['issue']} |")
    lines += ["", "## Guarded files (sha256)", ""]
    for path, digest in report["inputs"].items():
        lines.append(f"- `{path}` — `{(digest or 'missing')[:16]}…`")
    lines += ["", "Re-verify with "
              "`python scripts/audit_boundary.py --verify <this file>`."]
    return "\n".join(lines) + "\n"


def verify(path):
    recorded = json.loads(Path(path).read_text())
    fresh = audit()
    problems = []
    if recorded.get("contract") != fresh.get("contract"):
        problems.append(f"contract moved: report says {recorded.get('contract')}, "
                        f"now {fresh.get('contract')}")
    old = {row["check"]: row for row in recorded.get("checks", [])}
    for row in fresh["checks"]:
        before = old.get(row["check"])
        if before is None:
            problems.append(f"check {row['check']!r} was not in the report")
        elif before["exit"] != row["exit"]:
            problems.append(f"check {row['check']!r}: report had exit "
                            f"{before['exit']}, now {row['exit']}")
    changed = [path for path, digest in recorded.get("inputs", {}).items()
               if _sha(path) != digest]
    return problems, changed, fresh


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--verify" in argv:
        path = argv[argv.index("--verify") + 1]
        problems, changed, fresh = verify(path)
        if changed:
            print(f"inputs changed since the report ({len(changed)}): "
                  + ", ".join(changed))
        if problems:
            print("AUDIT VERIFY RED:")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print(f"audit verify: {len(fresh['checks'])} checks still exit as recorded; "
              f"contract {fresh['contract']} unchanged — OK")
        return 0
    report = audit()
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    if out:
        path = Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=1) + "\n")
        path.with_suffix(".md").write_text(_markdown(report))
        try:
            shown = path.resolve().relative_to(ROOT)
        except ValueError:
            shown = path
        print(f"audit: wrote {shown} and its .md "
              f"({report['verdict']}, {len(report['checks'])} checks)")
    else:
        print(json.dumps(report, indent=1))
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
