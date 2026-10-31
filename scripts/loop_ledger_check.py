#!/usr/bin/env python3
"""Loop ledger check (issue #240): the program review must match its data.

`docs/core/loop5-ledger.json` is the machine-readable record of the 100 loop-5
issues; `docs/core/program-review-loop5.md` is the review written from it. This
script keeps the two honest, offline:

  * the summary counts add up to the rows, and every row is structurally sound;
  * a `done` / `delivered, open` row names at least one commit, and a
    `not started` / `blocked` / `covered` / `partial` row names none;
  * commits recorded for **this** repo exist here and their subject names the
    issue (with `--repos <path>` the platform repo's commits are checked too);
  * the review's table has exactly the ledger's rows, status for status.

CI has this repo only, so cross-repo commits are skipped here unless `--repos`
is passed (the verify step in the review's own PR did pass it).

Usage:
  python scripts/loop_ledger_check.py [--repos /path/to/abn.platform.opengate] [--json]
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "docs" / "core" / "loop5-ledger.json"
REVIEW = ROOT / "docs" / "core" / "program-review-loop5.md"
STATUSES = {"done", "delivered_open", "covered", "partial", "blocked",
            "not_started", "this_review"}
LABELS = {"done": "done", "delivered_open": "delivered, open",
          "covered": "covered", "partial": "partial", "blocked": "blocked",
          "not_started": "not started", "this_review": "this review"}
SHA = re.compile(r"^[0-9a-f]{40}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ROW = re.compile(r"^\| (\d+) \| \[#(\d+)\]\([^)]*\) \| (.+?) \| ([a-z, ]+) \|",
                 re.M)


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def _commit_ok(repo_path, commit, number):
    sha = commit["sha"]
    if not SHA.match(sha) or commit["short"] != sha[:7]:
        return f"issue {number}: commit {sha!r} is not a 40-char sha with short {sha[:7]}"
    if not DATE.match(commit["date"]):
        return f"issue {number}: commit {sha[:7]} has no ISO date"
    probe = _git(["cat-file", "-e", f"{sha}^{{commit}}"], repo_path)
    if probe.returncode != 0:
        return (f"issue {number}: commit {sha[:7]} is not in {repo_path} — "
                f"the ledger and the repository disagree")
    subject = _git(["show", "-s", "--format=%s", sha], repo_path).stdout.strip()
    if not subject.startswith(f"Issue #{number}:"):
        return (f"issue {number}: commit {sha[:7]} subject does not start "
                f"with 'Issue #{number}:': {subject!r}")
    return None


def check(repos=None):
    problems = []
    try:
        ledger = json.loads(LEDGER.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{LEDGER}: {exc}"]
    if ledger.get("version") != 1:
        problems.append("ledger: version must be 1")
    if ledger.get("loop") != 5 or ledger.get("range") != [141, 240]:
        problems.append("ledger: loop/range must be 5 / [141, 240]")
    rows = ledger.get("issues")
    if not isinstance(rows, list) or not rows:
        return problems + ["ledger: issues must be a non-empty list"]

    numbers = [row.get("number") for row in rows]
    if numbers != sorted(numbers):
        problems.append("ledger: issues are not in number order")
    if len(set(numbers)) != len(numbers):
        problems.append("ledger: duplicate issue numbers")
    if set(numbers) != set(range(141, 241)):
        missing = sorted(set(range(141, 241)) - set(numbers))
        extra = sorted(set(numbers) - set(range(141, 241)))
        problems.append(f"ledger: issues must be 141..240 (missing {missing}, "
                        f"extra {extra})")

    counts = {key: 0 for key in STATUSES}
    for row in rows:
        number = row.get("number")
        status = row.get("status")
        if status not in STATUSES:
            problems.append(f"issue {number}: unknown status {status!r}")
            continue
        counts[status] += 1
        if not str(row.get("title") or "").startswith("L5-"):
            problems.append(f"issue {number}: title must start with 'L5-'")
        if row.get("state") not in ("closed", "open"):
            problems.append(f"issue {number}: state must be closed or open")
        if status == "done" and row.get("state") != "closed":
            problems.append(f"issue {number}: done but not closed")
        if status in ("covered", "partial", "blocked", "this_review") and not str(
                row.get("note") or "").strip():
            problems.append(f"issue {number}: {status} needs a note saying why")
        commits = row.get("commits") or []
        if status in ("done", "delivered_open") and not commits:
            problems.append(f"issue {number}: {status} needs at least one commit")
        if status not in ("done", "delivered_open") and commits:
            problems.append(f"issue {number}: {status} but names a commit")
        for commit in commits:
            repo = commit.get("repo")
            if repo not in ("opengate", "enterprise"):
                problems.append(f"issue {number}: unknown repo {repo!r}")
                continue
            if repo == "enterprise" or (repo == "opengate" and repos):
                where = ROOT if repo == "enterprise" else Path(repos)
                problem = _commit_ok(where, commit, number)
                if problem:
                    problems.append(problem)

    summary = ledger.get("summary") or {}
    for key, value in counts.items():
        if summary.get(key) != value:
            problems.append(f"ledger: summary.{key} = {summary.get(key)!r}, "
                            f"rows say {value}")
    scored = len(rows) - counts.get("this_review", 0)
    if summary.get("scored") != scored:
        problems.append(f"ledger: summary.scored = {summary.get('scored')!r}, "
                        f"rows say {scored}")
    if summary.get("total") != len(rows):
        problems.append(f"ledger: summary.total = {summary.get('total')!r}, "
                        f"rows say {len(rows)}")

    if not REVIEW.is_file():
        problems.append(f"{REVIEW}: missing")
        return problems
    seen = ROW.findall(REVIEW.read_text())
    if len(seen) != len(rows):
        problems.append(f"review: {len(seen)} table rows, ledger has {len(rows)}")
    by_number = {row["number"]: row for row in rows}
    for number, linked, _title, label in seen:
        row = by_number.get(int(number))
        if int(linked) != int(number):
            problems.append(f"review: row {number} links to #{linked}")
        if row is None:
            problems.append(f"review: row {number} is not in the ledger")
        elif LABELS[row["status"]] != label.strip():
            problems.append(f"review: row {number} says {label.strip()!r}, "
                            f"ledger says {LABELS[row['status']]!r}")
    return problems


def main():
    repos = None
    if "--repos" in sys.argv:
        index = sys.argv.index("--repos")
        try:
            repos = sys.argv[index + 1]
        except IndexError:
            print("loop-ledger: --repos needs a path", file=sys.stderr)
            return 2
    problems = check(repos)
    if "--json" in sys.argv:
        print(json.dumps(problems, indent=1))
    if problems:
        print("LOOP LEDGER RED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    ledger = json.loads(LEDGER.read_text())
    summary = ledger["summary"]
    skipped = 0 if repos else sum(
        1 for row in ledger["issues"] for commit in row["commits"]
        if commit["repo"] == "opengate")
    print(f"loop-ledger: {summary['total']} issues — {summary['done']} done, "
          f"{summary['delivered_open']} delivered/open, {summary['covered']} covered, "
          f"{summary['partial']} partial, {summary['blocked']} blocked, "
          f"{summary['not_started']} not started — review matches the ledger — OK"
          + (f" ({skipped} cross-repo commits not checked here)" if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
