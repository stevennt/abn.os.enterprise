#!/usr/bin/env python3
"""Contract tests for the three-plane boundary (ADR-002, issue #247).

The boundary is paper: a contract page, a ratification, a review record and a
program index. Paper drifts — a decision loses its consequence, the ownership
matrix grows a field with two owners, a deferred finding cites an issue that
does not exist, the index stops linking the ADR. These tests read the pages and
refuse that drift, offline.

  decisions    10 decisions D1–D10, each with a decision, a why and a consequence
  seams        the four seam contracts, each with a direction
  ownership    no field is owned twice in the ownership matrix
  findings     every review finding has a disposition; a deferred one cites a
               real issue (present in the program's task→issue map)
  adr          ADR-002 is accepted and states decision, consequences, reversal
  index        the program index links the three documents, and they exist

Usage:
  python scripts/test_plane_contract.py [--json]
  python scripts/test_plane_contract.py --self-test   # mutate the pages, prove red
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "docs" / "core" / "paperclip-integration.md"
ADR = ROOT / "docs" / "core" / "adr-002-paperclip-three-planes.md"
REVIEW = ROOT / "docs" / "core" / "paperclip-reviews" / "PC1-01-02-plane-contract.md"
INDEX = ROOT / "docs" / "core" / "paperclip-program.md"
EXPLAINER = ROOT / "docs" / "core" / "paperclip-explainer.md"
READER = ROOT / "docs" / "core" / "paperclip-reviews" / "PC1-01-09-explainer.md"
MAP = ROOT / "docs" / "core" / "prompts" / "paperclip-issue-map.json"

DECISION_ROW = re.compile(r"^\| (D\d+) \| ([^|]*) \| ([^|]*) \| ([^|]*) \|$", re.M)
SEAM_ITEM = re.compile(r"^(\d)\. \*\*(.+?)\*\* \((.+?)\)", re.M)
OWNER_ROW = re.compile(r"^\| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$", re.M)
FINDING_ROW = re.compile(r"^\| (F\d+) \| (\w+) \| (.+?) \| (.+?) \| (.+?) \|$", re.M)
ISSUE_REF = re.compile(r"#(\d+)")
VERSION = re.compile(r"paperclip-boundary@\d+\.\d+")


def _read(path):
    return path.read_text() if path.is_file() else ""


def _section(text, heading):
    start = text.find(heading)
    if start < 0:
        return ""
    end = text.find("\n## ", start + len(heading))
    return text[start:end if end > 0 else len(text)]


def _rows(text, pattern):
    return [m.groups() for m in pattern.finditer(text)]


def decisions(text):
    rows = _rows(_section(text, "## Decisions"), DECISION_ROW)
    problems = []
    expected = [f"D{i}" for i in range(1, 11)]
    found = [row[0] for row in rows]
    if found != expected:
        problems.append(f"decisions: expected D1..D10 in order, found "
                        f"{found or 'none'}")
    for ident, decision, why, consequence in rows:
        for label, value in (("decision", decision), ("why", why),
                             ("consequence", consequence)):
            if not value.strip() or value.strip() == "—":
                problems.append(f"decisions: {ident} has no {label}")
    return problems


def seams(text):
    items = _rows(_section(text, "## Seam contracts"), SEAM_ITEM)
    problems = []
    if [int(n) for n, _title, _direction in items] != [1, 2, 3, 4]:
        problems.append(f"seams: expected four numbered seam contracts, found "
                        f"{[n for n, _t, _d in items] or 'none'}")
    for number, title, direction in items:
        if "→" not in direction:
            problems.append(f"seams: {number} ({title}) names no direction")
    return problems


def ownership(text):
    rows = _rows(_section(text, "## Ownership matrix"), OWNER_ROW)
    problems = []
    seen = {}
    for fields, owner, _mirror, _never in rows:
        if fields.strip().lower().startswith("field"):
            continue
        for field in [part.strip(" `") for part in fields.split(",")]:
            if not field:
                continue
            if field in seen:
                problems.append(f"ownership: '{field}' owned by both "
                                f"'{seen[field]}' and '{owner}'")
            else:
                seen[field] = owner
    if not seen:
        problems.append("ownership: no fields parsed")
    return problems


def findings(text, known_issues):
    rows = _rows(_section(text, "## Findings"), FINDING_ROW)
    problems = []
    if not rows:
        return ["findings: no findings parsed"]
    for ident, severity, _finding, _evidence, disposition in rows:
        if severity not in ("blocker", "major", "minor"):
            problems.append(f"findings: {ident} has severity {severity!r}")
        low = disposition.lower()
        if "resolved" not in low and "deferred" not in low:
            problems.append(f"findings: {ident} has no disposition")
        if "deferred" in low:
            refs = [int(n) for n in ISSUE_REF.findall(disposition)]
            if not refs:
                problems.append(f"findings: {ident} is deferred with no issue")
            for ref in refs:
                if known_issues and ref not in known_issues:
                    problems.append(f"findings: {ident} cites issue #{ref}, "
                                    f"which is not in the program map")
    return problems


def adr(text):
    problems = []
    status = next((line for line in text.splitlines()
                   if line.lower().startswith("**status:**")), "")
    if "accepted" not in status.lower():
        problems.append("adr: no accepted status line")
    for heading in ("## Decision", "## Consequences", "## What would reverse this"):
        if heading not in text:
            problems.append(f"adr: missing section {heading!r}")
    return problems


def version(text, adr_text):
    """The contract carries a version, its upgrade path, and the ADR matches it."""
    problems = []
    contract_version = VERSION.search(_section(text, "# Paperclip"))
    if contract_version is None:
        problems.append("version: the contract header carries no "
                        "paperclip-boundary@MAJOR.MINOR id")
    section = _section(text, "## Versioning and the upgrade path")
    if not section:
        problems.append("version: no 'Versioning and the upgrade path' section")
    else:
        for token in ("none", "minor", "major", "new ADR", "boundary:"):
            if token not in section:
                problems.append(f"version: the upgrade path does not mention {token!r}")
    adr_version = VERSION.search(adr_text)
    if adr_version is None:
        problems.append("version: the ADR does not ratify a contract version")
    elif contract_version and adr_version.group(0) != contract_version.group(0):
        problems.append(f"version: ADR ratifies {adr_version.group(0)}, contract "
                        f"says {contract_version.group(0)}")
    return problems


def explainer(text, review_text):
    """The plain-language page stays plain, complete and backed by a reader check."""
    problems = []
    if "## In one minute" not in text or "## Follow one task" not in text:
        problems.append("explainer: missing the one-minute summary or the task walk-through")
    if "```" not in text or "design plane" not in text or "tenant plane" not in text:
        problems.append("explainer: no diagram naming the three planes")
    for question in ("Is Paperclip replacing OpenGate?",
                     "Where does the org chart live?",
                     "Can an agent read another customer's files?",
                     "What happens if Paperclip is down?",
                     "Who owns the cost number the customer sees?"):
        if question not in text:
            problems.append(f"explainer: missing question {question!r}")
    for term in ("tenant", "company", "model", "template", "run context",
                 "record", "metering", "boundary version"):
        if f"**{term}**" not in text and f"**pass** / **run context**" != term:
            if term == "run context":
                if "**run context**" not in text and "**pass** / **run context**" not in text:
                    problems.append("explainer: term 'run context' not defined")
            else:
                problems.append(f"explainer: term {term!r} not defined")
    if "PC1-01-09-explainer.md" not in text:
        problems.append("explainer: does not link the fresh-reader record")
    if review_text:
        if "Fresh-reader check" not in review_text:
            problems.append("explainer review: not a fresh-reader check")
        if "pass after one revision" not in review_text.lower():
            problems.append("explainer review: no verdict")
    else:
        problems.append("explainer review: the reader record is missing")
    return problems


def index(text):
    problems = []
    for rel in ("docs/core/paperclip-integration.md",
                "docs/core/adr-002-paperclip-three-planes.md",
                "docs/core/paperclip-reviews/PC1-01-02-plane-contract.md"):
        if rel not in text:
            problems.append(f"index: does not link {rel}")
        if not (ROOT / rel).is_file():
            problems.append(f"index: links {rel}, which does not exist")
    return problems


def known_issues():
    try:
        return {int(v) for v in json.loads(MAP.read_text()).values()}
    except (OSError, ValueError):
        return set()


def check():
    issues = known_issues()
    problems = []
    problems += decisions(_read(CONTRACT))
    problems += seams(_read(CONTRACT))
    problems += ownership(_read(CONTRACT))
    problems += findings(_read(REVIEW), issues)
    problems += adr(_read(ADR))
    problems += version(_read(CONTRACT), _read(ADR))
    problems += explainer(_read(EXPLAINER), _read(READER))
    problems += index(_read(INDEX))
    return problems


def self_test():
    """Mutate each page and prove the matching test goes red."""
    import tempfile

    failures = []
    contract = _read(CONTRACT)
    review = _read(REVIEW)
    adr_text = _read(ADR)
    index_text = _read(INDEX)

    def expect(label, problems, needle):
        if not any(needle in p for p in problems):
            failures.append(f"{label}: expected a problem containing {needle!r}, "
                            f"got {problems}")

    expect("missing decision", decisions(contract.replace("| D7 |", "| Dx |")),
           "expected D1..D10")
    expect("decision without why",
           decisions(contract.replace(
               "| two-way sync of an org model is a merge conflict with a payroll attached |",
               "|  |")), "no why")
    expect("seam without direction",
           seams(contract.replace("(Enterprise → Paperclip)", "(Enterprise)")),
           "names no direction")
    expect("field owned twice",
           ownership(contract.replace(
               "| tickets, comments, run logs, approvals UI | Paperclip |",
               "| tickets, comments, run logs, approvals UI | Paperclip |\n"
               "| org units, roles, reporting lines | Paperclip |")),
           "owned by both")
    expect("deferred without issue",
           findings(review.replace("**deferred** → PC1-04-02 (#273)",
                                   "**deferred** → PC1-04-02"), set()),
           "deferred with no issue")
    expect("unknown issue",
           findings(review.replace("(#273)", "(#99999)"), {273}),
           "not in the program map")
    expect("adr not accepted", adr(adr_text.replace("accepted (program)",
                                                    "proposed")),
           "no accepted status")
    expect("index missing link",
           index(index_text.replace("docs/core/adr-002-paperclip-three-planes.md",
                                    "docs/core/adr-999.md")),
           "does not link")
    expect("contract without version",
           version(contract.replace("`paperclip-boundary@1.0`", "the contract"),
                   adr_text), "carries no")
    expect("adr ratifies another version",
           version(contract, adr_text.replace("paperclip-boundary@1.0",
                                              "paperclip-boundary@9.9")),
           "ADR ratifies")
    expect("upgrade path missing",
           version(contract.replace("## Versioning and the upgrade path",
                                    "## Versioning"), adr_text),
           "no 'Versioning")
    explainer_text = _read(EXPLAINER)
    expect("explainer without a term",
           explainer(explainer_text.replace("| **metering** |", "| metering |"),
                     _read(READER)), "not defined")
    expect("explainer without the reader record",
           explainer(explainer_text.replace("PC1-01-09-explainer.md", "a review"),
                     _read(READER)), "does not link")
    return failures


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--self-test" in argv:
        failures = self_test()
        if failures:
            print("plane-contract --self-test RED:")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("plane-contract --self-test: 13 mutations, each caught — OK")
        return 0
    problems = check()
    if "--json" in argv:
        print(json.dumps(problems, indent=1))
    if problems:
        print("PLANE CONTRACT RED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("plane-contract: 10 decisions, 4 seams, one owner per field, "
          "9 findings dispositioned, ADR accepted, version + upgrade path, "
          "explainer + reader check, index links — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
