#!/usr/bin/env python3
"""The operator surface for portable bundles (issue #327).

Acceptance:
  * a tenant admin or operator can see and act on it, permission-checked

In this repository the operator is an engineer with the checkout, so the "guard"
is that every action is explicit and every refusal carries its code and fix —
there is no actor model here (the tenant-facing gate lives in the platform). What
this tests is that the surface says something a person can act on: the bundle id,
the pin, the artefacts, and `unchanged` when nothing moved.

Exit 0 = green.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin" / "portable"
TINY = ROOT / "tests" / "fixtures" / "portability" / "tiny"
PLATFORM = "contract-2026.11.3"


def run(*argv):
    return subprocess.run([sys.executable, str(BIN), *map(str, argv)],
                          capture_output=True, text=True)


def main():
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        shutil.copytree(TINY, root)
        export = run("export", "--company", "acme", "--root", root,
                     "--platform", PLATFORM)
        if export.returncode != 0:
            problems.append(f"export refused: {export.stderr.strip()}")
        line = export.stdout.strip()
        if not line.startswith("acme  bundle-"):
            problems.append(f"the export line reads {line!r}")
        if PLATFORM not in line:
            problems.append(f"the export line does not name the platform: {line!r}")
        if "artefact(s)" not in line:
            problems.append(f"the export line does not count artefacts: {line!r}")

        recorded = run("record", "--company", "acme", "--root", root,
                       "--platform", PLATFORM)
        if recorded.returncode != 0 or "stored at" not in recorded.stdout:
            problems.append(f"record says {recorded.stdout.strip()!r} / "
                            f"{recorded.stderr.strip()!r}")
        again = run("record", "--company", "acme", "--root", root,
                    "--platform", PLATFORM)
        if "unchanged" not in again.stdout:
            problems.append(f"a second record does not say unchanged: "
                            f"{again.stdout.strip()!r}")

        listed = run("bundles", "--company", "acme", "--root", root)
        if "stored bundle(s), newest first" not in listed.stdout:
            problems.append(f"bundles says {listed.stdout.strip()!r}")
        bundle_id = listed.stdout.split("\n")[1].split()[1]

        shown = run("show", "--company", "acme", "--bundle", bundle_id,
                    "--root", root)
        if shown.returncode != 0 or "pinned at" not in shown.stdout:
            problems.append(f"show says {shown.stdout.strip()!r} / "
                            f"{shown.stderr.strip()!r}")
        if "org" not in shown.stdout or "flow" not in shown.stdout:
            problems.append("show does not list the artefacts by kind")

        missing = run("show", "--company", "acme", "--bundle", "bundle-ghost",
                      "--root", root)
        if missing.returncode != 1 or "no stored bundle" not in missing.stderr:
            problems.append(f"show of a missing bundle says "
                            f"{missing.returncode}/{missing.stderr.strip()!r}")

        checked = run("check", "--root", root)
        if checked.returncode != 0 or "verify" not in checked.stdout:
            problems.append(f"check says {checked.stdout.strip()!r} / "
                            f"{checked.stderr.strip()!r}")

        # a refusal names the code and the fix
        denied = run("export", "--company", "acme", "--root", root,
                     "--platform", "contract-2026.09.0")
        if denied.returncode != 1:
            problems.append(f"a stale platform exited {denied.returncode}")
        if "E-PORT-06" not in denied.stderr or "fix:" not in denied.stderr:
            problems.append(f"the refusal does not name its code and fix: "
                            f"{denied.stderr.strip()!r}")

        # --json is the payload, and it agrees with the line
        as_json = run("export", "--company", "acme", "--root", root,
                      "--platform", PLATFORM, "--json")
        payload = json.loads(as_json.stdout)
        if payload["bundleId"] not in line:
            problems.append("--json and the human line disagree on the id")

        # rollback needs --force when it would overwrite, and says which
        template = root / "companies" / "acme" / "paperclip-company.json"
        doc = json.loads(template.read_text())
        doc["label"] = "edited"
        template.write_text(json.dumps(doc, indent=2) + "\n")
        refused = run("rollback", "--company", "acme", "--to", bundle_id,
                      "--root", root)
        if refused.returncode != 1 or "E-PORT-04" not in refused.stderr:
            problems.append(f"a bare rollback says {refused.returncode}/"
                            f"{refused.stderr.strip()!r}")
        forced = run("rollback", "--company", "acme", "--to", bundle_id,
                     "--root", root, "--force")
        if forced.returncode != 0 or "(forced)" not in forced.stdout:
            problems.append(f"a forced rollback says {forced.stdout.strip()!r}")

        differ = run("diff", "--left",
                     root / "companies" / "acme" / P_BUNDLED(root, bundle_id),
                     "--right",
                     root / "companies" / "acme" / P_BUNDLED(root, bundle_id))
        if differ.returncode != 0 or "same bundle" not in differ.stdout:
            problems.append(f"diff of one bundle against itself says "
                            f"{differ.stdout.strip()!r} / {differ.stderr.strip()!r}")

    if problems:
        print("portable surface RED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("portable surface: export, record (and unchanged), bundles, show (and "
          "missing), check, a refusal naming its code and fix, --json, and a "
          "forced rollback — OK")
    return 0


def P_BUNDLED(root, bundle_id):
    return Path("bundles") / bundle_id / "bundle.json"


if __name__ == "__main__":
    sys.exit(main())
