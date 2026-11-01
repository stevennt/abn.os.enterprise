#!/usr/bin/env python3
"""The portability runbook reproduces (issue #328).

Acceptance:
  * the doc has the exact commands and the expected output

Generated, not written: `scripts/portable_walkthrough.py` copies the tiny fixture
into a temp checkout and walks the surface; `--check` regenerates and diffs, so a
stale transcript fails.

Exit 0 = green.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "portable_walkthrough.py"
DOC = ROOT / "docs" / "core" / "portability-walkthrough.md"
CONTRACT = ROOT / "docs" / "core" / "portability.md"


def run(*argv):
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True, cwd=str(ROOT))


def main():
    problems = []
    checked = run("--check")
    if checked.returncode != 0:
        problems.append(f"the transcript does not reproduce: "
                        f"{(checked.stderr or checked.stdout).strip()[:400]}")

    text = DOC.read_text()
    for command in ("bin/portable export", "bin/portable record",
                    "bin/portable bundles", "bin/portable show",
                    "bin/portable import", "bin/portable rollback",
                    "bin/portable verify", "bin/portable diff",
                    "bin/portable check"):
        if command not in text:
            problems.append(f"the transcript never runs {command!r}")
    for expected in ("unchanged (already stored)", "E-PORT-06", "E-PORT-05",
                     "E-PORT-08", "(forced)", "the same bundle"):
        if expected not in text:
            problems.append(f"the transcript never shows {expected!r}")
    if "$TMP" not in text:
        problems.append("the transcript leaks a temporary path")
    if re.search(r"/var/folders/|/tmp/", text):
        problems.append("a raw temporary path leaked into the transcript")
    if re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", text):
        problems.append("an unnormalised timestamp leaked into the transcript")
    if "portability-walkthrough.md" not in CONTRACT.read_text():
        problems.append("the contract does not link the runbook")

    # a hand edit turns the check red, and the file is restored
    original = DOC.read_text()
    try:
        DOC.write_text(original + "\nhand-written line\n")
        red = run("--check")
        if red.returncode != 1 or "does not reproduce" not in red.stderr:
            problems.append("a hand edit did not turn --check red")
    finally:
        DOC.write_text(original)

    if problems:
        print("portability walkthrough RED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("portability walkthrough: reproduces, names every command and refusal, "
          "and a hand edit turns it red — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
