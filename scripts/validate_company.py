#!/usr/bin/env python3
"""validate_company — every company model in companies/*/company.yaml (#231).

A company model is one legal entity's operating model inside an OpenGate tenant,
built from this repo's contract and pinned to a contract release. This script
proves:

  1. the manifest validates against companies/company.schema.yaml;
  2. the id matches its directory, the industry exists and the adopted flows and
     rule packs exist in that industry;
  3. the org chart exists and every department's org_unit resolves to a unit;
  4. the contract pin resolves: the tag is a release tag, its sha is a real
     commit, and when the tag is present locally or on origin it points at that
     sha (offline: UNKNOWN warning, never a lie).

Usage: python scripts/validate_company.py [--json]
       python scripts/validate_company.py --self-test
"""
import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "companies" / "company.schema.yaml"


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text())


def sh(*args, check=False):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=check)


def local_tag_commit(tag):
    r = sh("git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}")
    return r.stdout.strip() if r.returncode == 0 else None


def remote_tag_commit(tag):
    r = sh("git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}")
    if r.returncode != 0:
        return None
    direct, peeled = None, None
    for line in r.stdout.splitlines():
        if "refs/tags/" not in line:
            continue
        sha, ref = line.split(maxsplit=1)
        if ref.endswith("^{}"):
            peeled = sha
        else:
            direct = sha
    return peeled or direct


def tag_commit(tag):
    return local_tag_commit(tag) or remote_tag_commit(tag)


def commit_exists(sha):
    return sh("git", "cat-file", "-e", f"{sha}^{{commit}}").returncode == 0


def chart_units(path):
    doc = load_yaml(path)
    if not isinstance(doc, list):
        raise ValueError("org chart must be a list of units")
    units = {}
    for entry in doc:
        if not isinstance(entry, dict) or not entry.get("id"):
            raise ValueError("every org unit needs an id")
        units[str(entry["id"])] = entry
    return units


def industry_flows(root, industry):
    ids = set()
    for path in sorted((root / "industries" / industry / "flows").glob("*.flow.yaml")):
        doc = load_yaml(path)
        if isinstance(doc, dict) and doc.get("id"):
            ids.add(str(doc["id"]))
    return ids


def industry_rule_packs(root, industry):
    return {path.stem for path in
            sorted((root / "industries" / industry / "rules").glob("*.yaml"))}


def validate_model(doc, root, schema, tag_lookup=None, commit_check=None):
    """(errors, warnings) for one company manifest."""
    tag_lookup = tag_lookup or tag_commit
    commit_check = commit_check or commit_exists
    errors = [f"schema: {error.message}"
              for error in jsonschema.Draft7Validator(schema).iter_errors(doc)]
    if errors:
        return errors, []
    warnings = []

    industry = str(doc["industry"]["id"])
    industry_dir = root / "industries" / industry
    if not (industry_dir / "industry.yaml").is_file():
        errors.append(f"industry {industry!r} does not exist")
        return errors, warnings

    contract = doc["contract"]
    tag, sha = str(contract["tag"]), str(contract["sha"])
    if not commit_check(sha):
        errors.append(f"contract sha {sha[:12]}… is not a commit in this repo")
    resolved = tag_lookup(tag)
    if resolved is None:
        warnings.append(f"contract tag {tag} not found locally or on origin — "
                        f"UNKNOWN (offline?), sha checked only")
    elif resolved != sha:
        errors.append(f"contract tag {tag} points at {resolved[:12]}…, "
                      f"but the pin says {sha[:12]}…")

    chart_path = root / "companies" / str(doc["id"]) / str(doc["org"]["chart"])
    try:
        units = chart_units(chart_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        errors.append(f"org chart {doc['org']['chart']}: {exc}")
        units = {}
    for unit_id, unit in units.items():
        parent = unit.get("parent_id")
        if parent is not None and str(parent) not in units:
            errors.append(f"org unit {unit_id!r} has unknown parent {parent!r}")

    seen = set()
    for department in doc["departments"]:
        did = str(department["id"])
        if did in seen:
            errors.append(f"duplicate department id {did!r}")
        seen.add(did)
        if units and str(department["org_unit"]) not in units:
            errors.append(f"department {did!r} maps to unknown org unit "
                          f"{department['org_unit']!r}")

    flows = industry_flows(root, industry)
    for flow_id in doc.get("flows") or []:
        if str(flow_id) not in flows:
            errors.append(f"flow {flow_id!r} is not part of industry {industry!r}")
    packs = industry_rule_packs(root, industry)
    for rule_pack in doc.get("rules") or []:
        if str(rule_pack) not in packs:
            errors.append(f"rule pack {rule_pack!r} is not part of industry "
                          f"{industry!r}")

    industry_pack = (doc.get("industry") or {}).get("pack")
    if industry_pack and not str(industry_pack).startswith(f"{industry}-pack-"):
        errors.append(f"industry pack {industry_pack!r} is not a {industry!r} pack")
    for pack_tag in doc.get("packs") or []:
        if not str(pack_tag).startswith(f"{industry}-pack-"):
            errors.append(f"pack {pack_tag!r} is not a {industry!r} pack release")
        elif tag_lookup(str(pack_tag)) is None:
            warnings.append(f"pack tag {pack_tag} not found locally or on origin — "
                            f"UNKNOWN (offline?)")

    status_doc = (doc.get("docs") or {}).get("status")
    if status_doc and not (root / "companies" / str(doc["id"]) / status_doc).is_file():
        errors.append(f"docs.status points at missing {status_doc}")
    return errors, warnings


def discover(root):
    return sorted(path for path in (root / "companies").glob("*/company.yaml"))


def self_test():
    schema = load_yaml(SCHEMA)
    example = load_yaml(ROOT / "companies" / "example-bank" / "company.yaml")
    sha = str(example["contract"]["sha"])

    def good(doc):
        return validate_model(doc, ROOT, schema,
                              tag_lookup=lambda tag: sha,
                              commit_check=lambda value: True)

    errors, _warnings = good(example)
    assert not errors, f"the example model must validate: {errors}"

    cases = {
        "unknown industry": lambda doc: doc["industry"].__setitem__("id", "nope"),
        "unknown flow": lambda doc: doc.__setitem__("flows", ["ghost.flow"]),
        "unknown rule pack": lambda doc: doc.__setitem__("rules", ["ghost-pack"]),
        "bad paperclip opt-in": lambda doc: doc.__setitem__(
            "paperclip", {"compile": "yes"}),
        "unknown org unit": lambda doc: doc["departments"][0].__setitem__(
            "org_unit", "ghost"),
        "tag mismatch": lambda doc: doc["contract"].__setitem__("sha", "0" * 40),
        "missing department": lambda doc: doc.__setitem__("departments", []),
    }
    for name, mutate in cases.items():
        doc = copy.deepcopy(example)
        mutate(doc)
        if name == "tag mismatch":
            errors, _ = validate_model(doc, ROOT, schema,
                                       tag_lookup=lambda tag: sha,
                                       commit_check=lambda value: True)
        else:
            errors, _ = good(doc)
        assert errors, f"fixture {name!r} should go red"
    print(f"self-test: example green, {len(cases)} broken fixtures red — OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    try:
        schema = load_yaml(SCHEMA)
    except (OSError, yaml.YAMLError) as exc:
        print(f"company: cannot load {SCHEMA.relative_to(ROOT)}: {exc}", file=sys.stderr)
        return 1

    results, failures, warnings_total = [], 0, 0
    for path in discover(ROOT):
        try:
            doc = load_yaml(path)
        except (OSError, yaml.YAMLError) as exc:
            results.append({"company": path.parent.name, "ok": False,
                            "errors": [f"unreadable: {exc}"], "warnings": []})
            failures += 1
            continue
        if isinstance(doc, dict) and doc.get("id") != path.parent.name:
            errors, warnings = [f"id {doc.get('id')!r} does not match directory "
                                f"{path.parent.name!r}"], []
        else:
            errors, warnings = validate_model(doc, ROOT, schema)
        results.append({"company": path.parent.name, "ok": not errors,
                        "errors": errors, "warnings": warnings})
        failures += 1 if errors else 0
        warnings_total += len(warnings)

    if args.json:
        print(json.dumps({"companies": results, "failures": failures,
                          "warnings": warnings_total}, indent=2))
    else:
        for row in results:
            mark = "OK" if row["ok"] else "FAIL"
            print(f"company {row['company']}: {mark}")
            for warning in row["warnings"]:
                print(f"  WARN {warning}")
            for error in row["errors"]:
                print(f"  FAIL {error}")
        print(f"companies: {len(results)} model(s), {failures} failure(s), "
              f"{warnings_total} warning(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
