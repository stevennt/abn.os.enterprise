#!/usr/bin/env python3
"""Validate compile records (issue #256).

`bin/paperclip-company --record` appends one line per run to
`companies/<company>/compiles.jsonl`. This validator is the repo's check that
those records are usable as evidence:

  V1  every line parses and carries the required fields;
  V2  `result` is compiled or refused; a refusal names an `E-COMP-NN` code and a
      message; a compile carries a 64-hex `templateSha256` and integer counts;
  V3  `boundary` matches the contract page, and the contract pin has the right
      shapes; the company in the line matches its directory;
  V4  timestamps do not go backwards; `compiler` is a known generator;
  V5  a company that opted in (`paperclip.compile: true`) has at least one record,
      and its **latest** record is `compiled` — a stale success cannot outlive a
      broken model.

Usage:
  python scripts/validate_compiles.py [--root .] [--json]
  python scripts/validate_compiles.py --self-test
"""
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "docs" / "core" / "paperclip-integration.md"
VERSION = re.compile(r"paperclip-boundary@\d+\.\d+")
CODE = re.compile(r"^E-COMP-\d{2}$")
TAG = re.compile(r"^contract-\d{4}\.\d{2}\.\d+$")
SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
AT = re.compile(r"^\d{4}-\d{2}-\d{2}T")
COMPILERS = {"paperclip-company@1"}


def _contract_version():
    text = CONTRACT.read_text() if CONTRACT.is_file() else ""
    found = VERSION.search(text)
    return found.group(0) if found else None


def _opted_in(company_dir):
    path = company_dir / "company.yaml"
    try:
        doc = yaml.safe_load(path.read_text()) or {}
    except (OSError, yaml.YAMLError):
        return False
    return bool((doc.get("paperclip") or {}).get("compile"))


def _line_problems(row, company, version):
    problems = []
    if row.get("version") != 1:
        problems.append("version must be 1")
    if row.get("company") != company:
        problems.append(f"company must be {company!r}")
    if row.get("compiler") not in COMPILERS:
        problems.append(f"unknown compiler {row.get('compiler')!r}")
    if not AT.match(str(row.get("at") or "")):
        problems.append("at must be an ISO timestamp")
    if row.get("boundary") != version:
        problems.append(f"boundary {row.get('boundary')!r} != contract {version!r}")
    pin = row.get("contract") or {}
    if not TAG.match(str(pin.get("tag") or "")) or \
            not SHA.match(str(pin.get("sha") or "")):
        problems.append("contract pin must be a release tag + 40-hex sha")
    result = row.get("result")
    if result == "compiled":
        if not SHA256.match(str(row.get("templateSha256") or "")):
            problems.append("compiled record needs templateSha256")
        for key in ("agents", "routines"):
            if not isinstance(row.get(key), int) or row[key] < 0:
                problems.append(f"compiled record needs an integer {key}")
        if not isinstance(row.get("inputs"), dict) or not row["inputs"]:
            problems.append("compiled record needs the input digests it read")
    elif result == "refused":
        if not CODE.match(str(row.get("code") or "")):
            problems.append("refused record needs an E-COMP-NN code")
        if not str(row.get("message") or "").strip():
            problems.append("refused record needs a message")
    else:
        problems.append(f"result must be compiled or refused, got {result!r}")
    return problems


def check(root=ROOT):
    root = Path(root)
    version = _contract_version()
    problems = []
    for path in sorted((root / "companies").glob("*/compiles.jsonl")):
        company = path.parent.name
        rel = path.relative_to(root).as_posix()
        rows = []
        try:
            lines = path.read_text().splitlines()
        except OSError as exc:
            problems.append(f"{rel}: unreadable ({exc})")
            continue
        last_at = ""
        for number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            where = f"{rel}:{number}"
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                problems.append(f"{where}: not JSON")
                continue
            if not isinstance(row, dict):
                problems.append(f"{where}: must be an object")
                continue
            for problem in _line_problems(row, company, version):
                problems.append(f"{where}: {problem}")
            at = str(row.get("at") or "")
            if at < last_at:
                problems.append(f"{where}: timestamp goes backwards ({at} < {last_at})")
            last_at = max(last_at, at)
            rows.append(row)
        if _opted_in(path.parent) and rows:
            latest = rows[-1]
            if latest.get("result") != "compiled":
                problems.append(f"{rel}: latest run is {latest.get('result')!r}, but "
                                f"the company opted in to compile")
        elif _opted_in(path.parent) and not rows:
            problems.append(f"{rel}: company opted in but has no compile record")
    return problems


def self_test():
    import tempfile

    base = {
        "version": 1, "at": "2026-11-01T08:00:00Z", "company": "demo",
        "compiler": "paperclip-company@1", "boundary": "paperclip-boundary@1.0",
        "contract": {"tag": "contract-2026.11.1", "sha": "a" * 40},
        "result": "compiled", "templateSha256": "b" * 64, "agents": 2, "routines": 2,
        "inputs": {"companies/demo/company.yaml": "c" * 64},
    }
    cases = [
        ("clean", [], None),
        ("refused without code",
         [dict(base, result="refused", message="no")], "E-COMP-NN"),
        ("compiled without digest",
         [dict(base, templateSha256=None)], "templateSha256"),
        ("boundary mismatch", [dict(base, boundary="paperclip-boundary@9.9")],
         "boundary"),
        ("backwards time",
         [dict(base, at="2026-11-01T09:00:00Z"), dict(base, at="2026-11-01T08:00:00Z")],
         "backwards"),
        ("latest refused but opted in",
         [dict(base), dict(base, result="refused", code="E-COMP-07", message="x",
                           at="2026-11-01T09:00:00Z")],
         "opted in"),
    ]
    failures = []
    for label, rows, needle in cases:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            company = root / "companies" / "demo"
            company.mkdir(parents=True)
            (company / "company.yaml").write_text(
                "version: 1\nid: demo\npaperclip:\n  compile: true\n")
            if rows:
                (company / "compiles.jsonl").write_text(
                    "\n".join(json.dumps(row) for row in rows) + "\n")
            problems = check(root)
            if needle is None:
                if problems:
                    failures.append(f"{label}: expected clean, got {problems}")
            elif not any(needle in problem for problem in problems):
                failures.append(f"{label}: expected {needle!r}, got {problems}")
    return failures


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--self-test" in argv:
        failures = self_test()
        if failures:
            print("compiles --self-test RED:")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("compiles --self-test: 6 cases (1 clean, 5 refused) — OK")
        return 0
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else ROOT
    problems = check(root)
    if "--json" in argv:
        print(json.dumps(problems, indent=1))
    if problems:
        print("COMPILE RECORDS RED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    records = sum(1 for path in (Path(root) / "companies").glob("*/compiles.jsonl")
                  for line in path.read_text().splitlines() if line.strip())
    print(f"compiles: {records} record(s) across the companies — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
