#!/usr/bin/env python3
"""Front-page link check (issue #139): README/ARCHITECTURE/ROADMAP and the
scorecard/cost templates must not point at paths that do not exist.

A front page that cites a directory which has since moved is worse than no front
page: it teaches the old shape to every new reader.

Usage: python scripts/docs_link_check.py [--json]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ["README.md", "ARCHITECTURE.md", "ROADMAP.md",
         "docs/core/scorecard.md", "docs/core/cost-model.md",
         "docs/core/onboarding-industry.md"]
PATHISH = re.compile(r"`([A-Za-z0-9_./\-]+\.(?:md|yaml|yml|py|json|ts|fga|tar\.gz))`")
# template placeholders and globs are not literal paths
SKIP = re.compile(r"<[^>]+>|\{[^}]+\}|\*")


def repo_basenames():
    """Index of basenames present anywhere in the repo.

    Prose often names a file without a path ("see MIGRATION.md", "run
    cross_industry.py"). Those are not dangling references if the file exists
    somewhere; a *path* whose directory no longer exists still fails,
    because basename lookup cannot rescue a wrong directory.
    """
    out = set()
    for q in ROOT.rglob("*"):
        if q.is_file() and ".git" not in q.parts and "build" not in q.parts:
            out.add(q.name)
    return out


def check(files=None):
    problems = []
    basenames = repo_basenames()
    for rel in (files or FILES):
        p = ROOT / rel
        if not p.is_file():
            problems.append(f"{rel}: file missing")
            continue
        for m in PATHISH.finditer(p.read_text()):
            ref = m.group(1)
            if SKIP.search(ref):
                continue
            # A bare filename may be prose ("see MIGRATION.md"); anything with a
            # directory component must resolve as an actual path, otherwise a
            # moved directory (examples/bank/...) would be rescued by basename.
            if "/" in ref:
                resolved = (ROOT / ref).exists() or (p.parent / ref).exists()
            else:
                resolved = (ROOT / ref).exists() or Path(ref).name in basenames
            if not resolved:
                problems.append(f"{rel}: dangling reference `{ref}`")
    return problems


def main():
    problems = check()
    if "--json" in sys.argv:
        print(json.dumps(problems, indent=1))
    if problems:
        print("DOCS LINK RED:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"docs-link: {len(FILES)} front-page docs, no dangling references — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
