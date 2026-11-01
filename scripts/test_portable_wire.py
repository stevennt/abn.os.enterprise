#!/usr/bin/env python3
"""The compiler emits a bundle, and the bundle round-trips (issue #324).

Acceptance:
  * the real run path uses it (no parallel implementation) and the integration
    test covers it

`bin/paperclip-company --bundle` is the real path: the compiler writes the template
and, beside it, the manifest the portability contract defines — through
`scripts/portable.py`, not a second implementation. This test compiles a fixture
company, verifies the bundle, imports it into a clean checkout, and diffs the two.

Exit 0 = green.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPILER = ROOT / "bin" / "paperclip-company"
PORTABLE = ROOT / "scripts" / "portable.py"
MODEL = ROOT / "tests" / "fixtures" / "paperclip-model"


def run(*argv):
    return subprocess.run([sys.executable, *map(str, argv)], capture_output=True,
                          text=True)


def main():
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        shutil.copytree(MODEL, root)
        out = root / "companies" / "demo" / "paperclip-company.json"

        compiled = run(COMPILER, "--root", root, "--company", "demo", "--out", out,
                       "--bundle")
        if compiled.returncode != 0:
            problems.append(f"the compiler refused a bundle: "
                            f"{(compiled.stderr or compiled.stdout).strip()}")
        manifest_path = out.parent / "bundle.json"
        if not manifest_path.is_file():
            problems.append("the compiler wrote no bundle.json beside the template")
        else:
            manifest = json.loads(manifest_path.read_text())
            if not manifest.get("bundleId", "").startswith("bundle-"):
                problems.append(f"the bundle id is {manifest.get('bundleId')!r}")
            if not manifest.get("artefacts"):
                problems.append("the bundle carries no artefacts")
            if manifest.get("template", {}).get("path") != \
                    "companies/demo/paperclip-company.json":
                problems.append(f"template.path is "
                                f"{manifest.get('template', {}).get('path')!r}")

        verified = run(PORTABLE, "verify", "--bundle", manifest_path, "--root", root)
        if verified.returncode != 0:
            problems.append(f"verify refused its own bundle: "
                            f"{(verified.stderr or verified.stdout).strip()}")

        # import into a checkout that does not have the template yet
        empty = Path(tmp) / "import"
        shutil.copytree(MODEL, empty)
        (empty / "companies" / "demo" / "paperclip-company.json").unlink(
            missing_ok=True)
        bundle_dir = Path(tmp) / "handover"
        bundle_dir.mkdir()
        shutil.copyfile(manifest_path, bundle_dir / "bundle.json")
        shutil.copyfile(out, bundle_dir / out.name)

        imported = run(PORTABLE, "import", "--bundle", bundle_dir / "bundle.json",
                       "--root", empty, "--platform", "contract-2026.11.1")
        if imported.returncode != 0:
            problems.append(f"import refused: "
                            f"{(imported.stderr or imported.stdout).strip()}")
        else:
            again = run(PORTABLE, "export", "--company", "demo", "--root", empty,
                        "--platform", "contract-2026.11.1")
            if again.returncode != 0:
                problems.append("the imported checkout does not export again")
            else:
                copy = Path(tmp) / "again.json"
                copy.write_text(again.stdout)
                differ = run(PORTABLE, "diff", "--left", manifest_path,
                             "--right", copy)
                if differ.returncode != 0:
                    problems.append("diff failed on a round trip")
                else:
                    report = json.loads(differ.stdout)
                    if not report.get("same") or report["added"] or \
                            report["removed"] or report["changed"]:
                        problems.append(f"the round trip is not the same bundle: "
                                        f"{report}")

            # a tampered artefact is refused by verify
            flow = next((empty / "companies" / "demo").rglob("*.flow.yaml"), None)
            if flow is not None:
                flow.write_text(flow.read_text() + "\n# edited\n")
                tampered = run(PORTABLE, "verify", "--bundle",
                               bundle_dir / "bundle.json", "--root", empty)
                if tampered.returncode == 0:
                    problems.append("verify accepted a tampered artefact")

    if problems:
        print("portable wire RED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("portable wire: compile → bundle → verify → import → diff, and a "
          "tampered artefact refused — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
