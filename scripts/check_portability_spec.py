#!/usr/bin/env python3
"""Portable-bundle checker (issue #322, `company-portability@1`).

Builds the manifest from a case's inputs (template pin, cited artefacts, the
platform it is going to), compares it with the committed one, and reports the
seven refusals in their contract order.

Usage:
    python scripts/check_portability_spec.py [path]
    python scripts/check_portability_spec.py --self-test
    python scripts/check_portability_spec.py --emit [path]

Exit 0 = green. `--self-test` mutates the case seven ways and proves each code
fires for its own reason; it is what CI runs beside the plain check.
"""
import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "portability-manifest.json"
CASE = ROOT / "tests" / "fixtures" / "portability" / "case.valid.json"

CODES = ("E-PORT-01", "E-PORT-02", "E-PORT-03", "E-PORT-04", "E-PORT-05",
         "E-PORT-06", "E-PORT-07")
TAG_RE = re.compile(r"^contract-([0-9]{4})\.([0-9]{2})\.([0-9]+)$")
FIX = {
    "E-PORT-01": "fix the export; the importer does not guess",
    "E-PORT-02": "fix the compile (E-COMP-02); a bundle without a pin is not "
                 "portable",
    "E-PORT-03": "re-export with the whole set; a partial bundle is a trap",
    "E-PORT-04": "stop: the bundle was altered in transit, or two versions were "
                 "mixed",
    "E-PORT-05": "strip it; company portability never moves a tenant's documents",
    "E-PORT-06": "upgrade the platform first; the importer must not silently "
                 "drop what it cannot read",
    "E-PORT-07": "make it relative to the repository root; an absolute path is a "
                 "bundle that only works on its own machine",
}


def _tag(value):
    match = TAG_RE.match(str(value or ""))
    return tuple(int(part) for part in match.groups()) if match else None


def _refusal(code, reason):
    return {"code": code, "reason": reason, "fix": FIX[code]}


def _bundle_id(company, template_sha, artefacts):
    lines = [f"{row['kind']}:{row['id']}@{row['version']}:{row['sha256']}"
             for row in sorted(artefacts, key=lambda row: (row["kind"], row["id"]))]
    blob = "\n".join([str(company), str(template_sha)] + lines)
    return "bundle-" + hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def check(case):
    """(manifest | None, [refusal…]) by the contract's ordered procedure."""
    template = case.get("template") or {}
    company = str(case.get("company") or "")
    contract = template.get("contract") or {}
    platform = str((case.get("platform") or {}).get("contractTag") or "")
    findings = []

    if not company or not template.get("path") or not template.get("sha256"):
        return None, [_refusal("E-PORT-01", "the case is missing the company, the "
                                           "template path or its digest")]
    tag = _tag(contract.get("tag"))
    if tag is None or not re.match(r"^[0-9a-f]{40}$", str(contract.get("sha") or "")):
        return None, [_refusal("E-PORT-02", f"the template's contract pin is "
                                           f"{contract!r}; a bundle without a pin "
                                           f"is not portable")]

    cited = {(row["kind"], row["id"]) for row in template.get("cites") or []}
    shipped = {(row["kind"], row["id"]): row
               for row in case.get("artefacts") or []}
    for key in sorted(cited - set(shipped)):
        findings.append(_refusal("E-PORT-03", f"the template cites {key[0]} "
                                              f"{key[1]!r}, which the bundle does "
                                              f"not carry"))
    for key in sorted(cited & set(shipped)):
        want = next(row for row in template["cites"]
                    if (row["kind"], row["id"]) == key)
        got = shipped[key]
        if str(want.get("version")) != str(got.get("version")) \
                or str(want.get("sha256")) != str(got.get("sha256")):
            findings.append(_refusal(
                "E-PORT-04", f"{key[0]} {key[1]!r}: the bundle says "
                             f"{got.get('version')}/{str(got.get('sha256'))[:12]}…, "
                             f"the template cites {want.get('version')}/"
                             f"{str(want.get('sha256'))[:12]}…"))

    artefacts = sorted(({"kind": row["kind"], "id": row["id"],
                         "version": row["version"], "sha256": row["sha256"]}
                        for row in (case.get("artefacts") or [])),
                       key=lambda row: (row["kind"], row["id"]))
    for row in artefacts:
        if str(row.get("kind")) == "tenant" or str(row.get("id")).startswith(
                "customers/"):
            findings.append(_refusal("E-PORT-05", f"{row['kind']} {row['id']!r} "
                                                  f"is tenant data"))
    for value in (template.get("path"), company):
        if str(value or "").startswith("/") or "file://" in str(value or ""):
            findings.append(_refusal("E-PORT-07", f"{value!r} is an absolute path "
                                                  f"or a machine root"))

    platform_tag = _tag(platform)
    if platform_tag is None:
        findings.append(_refusal("E-PORT-01", f"the platform pin {platform!r} is "
                                              f"not a contract tag"))
    elif tag > platform_tag:
        findings.append(_refusal(
            "E-PORT-06", f"the bundle was compiled against "
                         f"{contract['tag']} and the platform is pinned at "
                         f"{platform} — the importer would drop what it cannot "
                         f"read"))

    manifest = {"version": 1, "contract": "company-portability@1",
                "company": company,
                "bundleId": _bundle_id(company, template["sha256"], artefacts),
                "createdAt": str(case.get("createdAt")),
                "template": {"path": str(template["path"]),
                             "sha256": str(template["sha256"]),
                             "contract": {"tag": str(contract["tag"]),
                                          "sha": str(contract["sha"])}},
                "artefacts": artefacts,
                "platform": {"contractTag": platform}}
    return manifest, findings


def problems(case):
    found = []
    expected = case.get("expected") or {}
    computed, findings = check(case)
    if computed is None:
        return [f"the case cannot be checked: {findings[0]['reason']}"]
    if [row["code"] for row in findings] != [row["code"] for row in
                                            expected.get("findings") or []]:
        found.append("findings: committed "
                     f"{[row['code'] for row in expected.get('findings') or []]} "
                     f"!= computed {[row['code'] for row in findings]}")
    for want, got in zip(expected.get("findings") or [], findings):
        if want.get("reason") != got.get("reason"):
            found.append(f"{got['code']} reason: committed {want.get('reason')!r} "
                         f"!= computed {got.get('reason')!r}")
    schema = json.loads(SCHEMA.read_text())
    try:
        jsonschema.validate(computed, schema)
    except jsonschema.exceptions.ValidationError as exc:
        where = "/".join(str(part) for part in exc.absolute_path) or "manifest"
        found.append(f"manifest {where}: {exc.message}")
    for key, value in (expected.get("manifest") or {}).items():
        if computed.get(key) != value:
            found.append(f"manifest {key}: committed "
                         f"{json.dumps(value)[:80]} != computed "
                         f"{json.dumps(computed.get(key))[:80]}")
    return found


def _mutations(case):
    """Seven ways to be wrong; each must produce its code."""
    cases = []

    doc = copy.deepcopy(case)
    doc["company"] = ""
    cases.append(("E-PORT-01", "a case without a company", doc))

    doc = copy.deepcopy(case)
    doc["template"]["contract"] = {"tag": "v1", "sha": "abc"}
    cases.append(("E-PORT-02", "an unpinned template", doc))

    doc = copy.deepcopy(case)
    doc["template"]["cites"].append({"kind": "flow", "id": "credit-flow",
                                     "version": "2.0.0",
                                     "sha256": "b" * 64})
    cases.append(("E-PORT-03", "a cited artefact the bundle omits", doc))

    doc = copy.deepcopy(case)
    doc["artefacts"][0]["version"] = "2026.11.9"
    cases.append(("E-PORT-04", "an artefact that does not match its cite", doc))

    doc = copy.deepcopy(case)
    doc["artefacts"].append({"kind": "tenant", "id": "customers/acme/org.json",
                             "version": "1", "sha256": "c" * 64})
    cases.append(("E-PORT-05", "tenant data in a company bundle", doc))

    doc = copy.deepcopy(case)
    doc["platform"] = {"contractTag": "contract-2026.09.0"}
    cases.append(("E-PORT-06", "a bundle newer than the platform", doc))

    doc = copy.deepcopy(case)
    doc["template"]["path"] = "/Users/someone/companies/example-bank/paperclip-company.json"
    cases.append(("E-PORT-07", "an absolute template path", doc))
    return cases


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=str(CASE))
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--emit", action="store_true")
    args = ap.parse_args(argv)

    case = json.loads(Path(args.path).read_text())
    if args.emit:
        computed, findings = check(case)
        print(json.dumps({"manifest": computed, "findings": findings},
                         indent=2, ensure_ascii=False))
        return 0

    found = problems(case)
    if found:
        print(f"portability: {args.path} FAIL", file=sys.stderr)
        for problem in found:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    if args.self_test:
        missed = []
        for code, label, doc in _mutations(case):
            computed, findings = check(doc)
            codes = {row["code"] for row in findings}
            if code not in codes:
                missed.append(f"{label} (wanted {code}, got {sorted(codes)})")
        if missed:
            print("portability --self-test RED: " + "; ".join(missed),
                  file=sys.stderr)
            return 1
        print(f"portability --self-test: {len(_mutations(case))} mutations "
              f"refused, the committed bundle verifies — OK")
        return 0

    computed, findings = check(case)
    if args.json:
        print(json.dumps({"bundle": computed["bundleId"],
                          "artefacts": len(computed["artefacts"]),
                          "findings": [row["code"] for row in findings]},
                         indent=1))
        return 0
    print(f"portability: {computed['company']} {computed['bundleId']} — "
          f"{len(computed['artefacts'])} artefact(s), "
          f"{len(findings)} finding(s): "
          f"{', '.join(row['code'] for row in findings) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
