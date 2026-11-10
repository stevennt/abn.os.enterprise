#!/usr/bin/env python3
"""Field-ownership checker for `sync-semantics@1` (issue #482).

The register is the machine form of `docs/core/sync-semantics.md`: one row per field that
crosses a plane boundary — its owning plane, the planes that receive a copy, and the planes
that may never originate a write — plus the stream that carries it and the watermark that
makes a replay a no-op. This checker is the gate that turns *"we have a sync rule"* into a
question somebody can answer wrongly.

    E-SYN-01  the registry is not an object, or cannot be read
    E-SYN-02  `version` is not 1
    E-SYN-03  a field is not an object, or is missing a required key
    E-SYN-04  two fields share an id
    E-SYN-05  the plane list is not exactly the four planes
    E-SYN-06  a field does not have exactly one writer (a plane left unaccounted for)
    E-SYN-07  a field names an undeclared stream, a stream is duplicated, or a stream is empty
    E-SYN-08  a stream is not one-way, or a field's owner is not the stream's producer
    E-SYN-09  a field the document does not print (the register and the prose disagree)
    E-SYN-10  a stream with no watermark, or one that is not monotonic / not a no-op on replay
    E-SYN-11  a company-model field with no ownership row
    E-SYN-12  an ownership row for a `model.*` field the company schema does not have

`--company <dir>` also walks a real company model, so the day somebody adds a field to the
model without saying whose it is, this exits 1.

Usage:
    python3 scripts/check_sync_spec.py [registry.json] [--company companies/<id>]
    python3 scripts/check_sync_spec.py --self-test
    python3 scripts/check_sync_spec.py --json

Exit 0 = green, 1 = findings, 2 = the arguments were wrong.
"""

import argparse
import copy
import json
import re
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "field-ownership.json"
REGISTER = ROOT / "tests" / "fixtures" / "sync" / "field-ownership.json"
DOC = ROOT / "docs" / "core" / "sync-semantics.md"
COMPANY_SCHEMA = ROOT / "companies" / "company.schema.yaml"

PLANES = ("enterprise", "paperclip", "opengate", "vault")
REQUIRED = ("id", "stream", "owner", "mirroredTo", "neverWrittenBy", "sensitivity")

FIX = {
    "E-SYN-01": "point the check at a registry, or write one: "
                "{version: 1, planes, streams, fields}",
    "E-SYN-02": "a registry is version 1 (`sync-semantics@1`); an old one is migrated, "
                "not read",
    "E-SYN-03": "name the field's id, stream, owner, mirrors, the planes that may not "
                "write it, and its sensitivity",
    "E-SYN-04": "an id is a name: two rows with one id make every reference ambiguous",
    "E-SYN-05": "the planes are enterprise, paperclip, opengate, vault — all four, no others",
    "E-SYN-06": "every plane except the owner may never originate a write; say so, or the "
                "writer nobody granted is the one to blame",
    "E-SYN-07": "a field belongs to a declared stream, and a stream that carries nothing "
                "is a name with no meaning",
    "E-SYN-08": "one producer per stream — a second owner in one stream is the dual write "
                "this contract forbids",
    "E-SYN-09": "print the row: the register is the document's machine form, and a field "
                "nobody can read about is a field nobody follows",
    "E-SYN-10": "every stream carries a strictly increasing sequence and treats a "
                "re-delivery as already applied",
    "E-SYN-11": "add the row: a model field nobody owns is a field two planes will "
                "eventually write",
    "E-SYN-12": "delete the row, or add the field to companies/company.schema.yaml — the "
                "registry tracks the schema, not the other way round",
}


def _problem(code, detail):
    return {"code": code, "detail": detail, "fix": FIX[code]}


def _documented(text):
    """The field ids the document prints (`| `model.id` | …`)."""
    return set(re.findall(r"^\|\s*`([a-z-]+\.[A-Za-z][A-Za-z0-9_.]*)`\s*\|", text, re.M))


def _model_properties(root=ROOT):
    """The company model's top-level properties, from its schema."""
    try:
        schema = yaml.safe_load((Path(root) / "companies" / "company.schema.yaml").read_text())
    except (OSError, yaml.YAMLError):
        return None
    return set((schema or {}).get("properties") or {})


def _company_keys(where, root=ROOT):
    """The top-level keys of one company model, or None when it cannot be read."""
    base = Path(where)
    if not base.is_absolute():
        base = Path(root) / base
    model = base / "company.yaml"
    if not model.is_file():
        return None
    try:
        document = yaml.safe_load(model.read_text())
    except yaml.YAMLError:
        return None
    return set(document) if isinstance(document, dict) else None


def check(registry, root=ROOT, document=None, company=None):
    """Every finding, in code order."""
    if not isinstance(registry, dict):
        return [_problem("E-SYN-01", "the registry is not an object")]
    findings = []
    try:
        jsonschema.validate(registry, json.loads(SCHEMA.read_text()))
    except jsonschema.ValidationError as exc:
        path = "/".join(str(part) for part in exc.absolute_path)
        findings.append(_map(exc, path))
    if registry.get("version") != 1:
        findings.append(_problem("E-SYN-02", f"version is {registry.get('version')!r}"))
        return findings

    planes = registry.get("planes")
    if not isinstance(planes, list) or set(planes) != set(PLANES) or len(planes) != len(PLANES):
        findings.append(_problem("E-SYN-05",
                                 f"planes is {planes!r}, not the four known planes"))
        return findings

    streams = registry.get("streams")
    if not isinstance(streams, list):
        findings.append(_problem("E-SYN-07", "streams is not a list"))
        return findings
    declared = {}
    for index, stream in enumerate(streams):
        if not isinstance(stream, dict):
            findings.append(_problem("E-SYN-07", f"stream {index} is not an object"))
            continue
        name = stream.get("id")
        if name in declared:
            findings.append(_problem("E-SYN-07", f"stream {name!r} appears twice"))
        declared[name] = stream
        if stream.get("producer") not in PLANES:
            findings.append(_problem("E-SYN-05",
                                     f"stream {name!r}: producer "
                                     f"{stream.get('producer')!r} is not a plane"))
        if stream.get("direction") != "one-way":
            findings.append(_problem("E-SYN-08",
                                     f"stream {name!r}: direction "
                                     f"{stream.get('direction')!r}"))
        watermark = stream.get("watermark")
        if not isinstance(watermark, dict):
            findings.append(_problem("E-SYN-10", f"stream {name!r}: no watermark"))
            continue
        if watermark.get("monotonic") is not True:
            findings.append(_problem("E-SYN-10",
                                     f"stream {name!r}: the watermark is not monotonic"))
        if watermark.get("onReplay") != "no-op":
            findings.append(_problem("E-SYN-10",
                                     f"stream {name!r}: a replay is "
                                     f"{watermark.get('onReplay')!r}, not a no-op"))
        if not str(watermark.get("field") or "").strip():
            findings.append(_problem("E-SYN-10", f"stream {name!r}: the watermark has no "
                                                f"field to read"))

    fields = registry.get("fields")
    if not isinstance(fields, list):
        findings.append(_problem("E-SYN-03", "fields is not a list"))
        return findings
    seen = set()
    carried = {}
    for index, field in enumerate(fields):
        if not isinstance(field, dict):
            findings.append(_problem("E-SYN-03", f"field {index} is not an object"))
            continue
        missing = [key for key in REQUIRED if key not in field]
        if missing:
            findings.append(_problem("E-SYN-03",
                                     f"field {index} is missing {', '.join(missing)}"))
            continue
        name = field["id"]
        if name in seen:
            findings.append(_problem("E-SYN-04", f"{name} appears twice"))
        seen.add(name)

        owner = field.get("owner")
        mirrors = field.get("mirroredTo") or []
        forbidden = field.get("neverWrittenBy") or []
        if owner not in PLANES:
            findings.append(_problem("E-SYN-05", f"{name}: owner {owner!r} is not a plane"))
            continue
        unexplained = set(PLANES) - {owner} - set(forbidden)
        if unexplained:
            findings.append(_problem("E-SYN-06",
                                     f"{name}: no row says whether "
                                     f"{', '.join(sorted(unexplained))} may write it"))
        extra = set(forbidden) - (set(PLANES) - {owner})
        if extra:
            findings.append(_problem("E-SYN-06",
                                     f"{name}: neverWrittenBy names "
                                     f"{', '.join(sorted(extra))}, which is the owner or "
                                     f"not a plane"))
        if owner in mirrors:
            findings.append(_problem("E-SYN-06",
                                     f"{name}: the owner {owner!r} is also its own mirror"))

        stream = declared.get(field.get("stream"))
        if stream is None:
            findings.append(_problem("E-SYN-07",
                                     f"{name}: stream {field.get('stream')!r} is not "
                                     f"declared"))
        else:
            carried[stream["id"]] = carried.get(stream["id"], 0) + 1
            if stream.get("producer") != owner:
                findings.append(_problem("E-SYN-08",
                                         f"{name}: owned by {owner!r} but its stream is "
                                         f"produced by {stream.get('producer')!r}"))
    for name, stream in declared.items():
        if isinstance(stream, dict) and not carried.get(name):
            findings.append(_problem("E-SYN-07", f"stream {name!r} carries no field"))

    if document is not None:
        printed = _documented(document)
        for field in fields:
            if isinstance(field, dict) and field.get("id") not in printed:
                findings.append(_problem("E-SYN-09",
                                         f"{field.get('id')} is in the register and not in "
                                         f"the document"))

    properties = _model_properties(root)
    if properties:
        owned = {field.get("id") for field in fields if isinstance(field, dict)}
        for name in sorted(properties):
            if f"model.{name}" not in owned:
                findings.append(_problem("E-SYN-11",
                                         f"companies/company.schema.yaml declares {name!r} "
                                         f"and no row owns model.{name}"))
        for name in sorted(one for one in owned
                           if isinstance(one, str) and one.startswith("model.")):
            property_ = name[len("model."):]
            if property_ not in properties:
                findings.append(_problem("E-SYN-12",
                                         f"{name} has a row, and the company schema has no "
                                         f"{property_!r}"))

    if company:
        keys = _company_keys(company, root)
        if keys is None:
            findings.append(_problem("E-SYN-01", f"{company}: no company.yaml to read"))
        else:
            owned = {field.get("id") for field in fields if isinstance(field, dict)}
            for name in sorted(keys):
                if f"model.{name}" not in owned:
                    findings.append(_problem("E-SYN-11",
                                             f"{company}: the model has {name!r} and no row "
                                             f"owns model.{name}"))
    return findings


def _map(exc, path):
    """A schema failure as the code that names the rule, not as a jsonschema trace."""
    parts = path.split("/") if path else []
    where = f"stream {parts[1]}" if parts[:1] == ["streams"] and len(parts) > 1 else (
        f"field {parts[1]}" if parts[:1] == ["fields"] and len(parts) > 1 else "")
    if path.endswith("version"):
        return _problem("E-SYN-02", f"version {exc.instance!r}")
    if path.startswith("planes"):
        return _problem("E-SYN-05", f"planes {exc.instance!r}")
    if "direction" in path:
        return _problem("E-SYN-08", f"{where}: direction {exc.instance!r}")
    if "watermark" in path:
        return _problem("E-SYN-10", f"{where}: the watermark is not a strictly increasing "
                                    f"counter that no-ops on replay")
    if path.endswith("neverWrittenBy") or path.endswith("mirroredTo"):
        return _problem("E-SYN-06", f"{where}: {exc.instance!r}")
    if path.endswith("owner"):
        return _problem("E-SYN-05", f"{where}: owner {exc.instance!r}")
    if path.endswith("stream"):
        return _problem("E-SYN-07", f"{where}: stream {exc.instance!r}")
    if "is a required property" in exc.message:
        name = exc.message.split()[0].strip("'\"")
        return _problem("E-SYN-03", f"{where} is missing {name!r}")
    return _problem("E-SYN-03", f"{path or 'the registry'}: {exc.message[:80]}")


def verdict(findings):
    """(ok, blocking) — nothing here blocks alone; every finding is a shape to fix."""
    return not findings, []


def self_test():
    """Every code fires from a valid registry, and a valid registry stays quiet."""
    good = json.loads(REGISTER.read_text())
    document = DOC.read_text()
    if check(good, document=document):
        print(f"self-test RED: the committed registry was refused: "
              f"{check(good, document=document)}", file=sys.stderr)
        return 1

    def mutate(**changes):
        return dict(copy.deepcopy(good), **changes)

    def field_(index, **changes):
        fields = copy.deepcopy(good["fields"])
        fields[index] = dict(fields[index], **changes)
        return mutate(fields=fields)

    def stream_(index, **changes):
        streams = copy.deepcopy(good["streams"])
        streams[index] = dict(streams[index], **changes)
        return mutate(streams=streams)

    fields = copy.deepcopy(good["fields"])
    streams = copy.deepcopy(good["streams"])
    extra = {"id": "model.nonexistent", "stream": "model", "owner": "enterprise",
             "mirroredTo": ["paperclip"],
             "neverWrittenBy": [p for p in PLANES if p != "enterprise"],
             "sensitivity": "internal"}
    mutations = {
        "E-SYN-01": "not an object",
        "E-SYN-02": mutate(version=0),
        "E-SYN-03": mutate(fields=[{k: v for k, v in fields[0].items() if k != "owner"}]),
        "E-SYN-04": mutate(fields=fields + [fields[0]]),
        "E-SYN-05": mutate(planes=["enterprise", "paperclip", "opengate"]),
        "E-SYN-06": field_(0, neverWrittenBy=["paperclip", "opengate"]),
        "E-SYN-07": field_(0, stream="nobody"),
        "E-SYN-08": stream_(0, direction="two-way"),
        "E-SYN-09": mutate(fields=[dict(one) for one in fields]),
        "E-SYN-10": stream_(0, watermark={"field": "model.seq", "monotonic": False,
                                          "onReplay": "no-op"}),
        "E-SYN-11": mutate(fields=[one for one in fields if one["id"] != "model.label"]),
        "E-SYN-12": mutate(fields=fields + [extra]),
    }
    seen = set()
    for expected, registry in mutations.items():
        # E-SYN-09 is "a field the document does not print": the document is emptied
        findings = check(registry, document="" if expected == "E-SYN-09" else document)
        found = {one["code"] for one in findings}
        if expected not in found:
            print(f"self-test RED: {expected} did not fire — got {sorted(found) or 'nothing'}",
                  file=sys.stderr)
            return 1
        for one in findings:
            if not one["fix"]:
                print(f"self-test RED: {one['code']} has no fix", file=sys.stderr)
                return 1
        seen |= {one["code"] for one in findings}
        print(f"self-test: {expected} fired — {next(one['detail'] for one in findings if one['code'] == expected)}")
    if seen - set(mutations):
        print(f"self-test: also fired {sorted(seen - set(mutations))} (expected, from the "
              f"same mutations)", file=sys.stderr)
    print(f"self-test: all {len(mutations)} codes fire, and a valid registry stays quiet — OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="check_sync_spec")
    ap.add_argument("register", nargs="?", default=str(REGISTER))
    ap.add_argument("--company", default=None,
                    help="also check one company model's keys for an ownership row")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    try:
        registry = json.loads(Path(args.register).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        findings = [_problem("E-SYN-01", f"{args.register}: {exc}")]
        registry = None
    else:
        findings = check(registry, document=DOC.read_text(), company=args.company)

    ok, blocking = verdict(findings)
    if args.json:
        print(json.dumps({"ok": ok, "findings": findings, "blocking": blocking},
                         indent=2, ensure_ascii=False))
    else:
        if ok:
            line = (f"sync-semantics@1: {len(registry['fields'])} fields in "
                    f"{len(registry['streams'])} streams, one writer each")
            if args.company:
                keys = _company_keys(args.company) or ()
                line += (f" — {args.company}: {len(keys)} model key(s), every one owned")
            print(line + " — OK")
        for one in findings:
            print(f"{one['code']}: {one['detail']} — fix: {one['fix']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
