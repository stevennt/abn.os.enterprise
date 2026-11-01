#!/usr/bin/env python3
"""Plane-boundary check (ADR-002, issue #246): the model repo must not drift
into the execution or tenant planes.

The contract (`docs/core/paperclip-integration.md`) says this repository owns the
*design* plane: org, roles, processes, rules, touchpoints, packs, companies and
the contract pin. Paperclip owns work state (tickets, checkouts, heartbeats,
runs); OpenGate owns the tenant (folders, ACL, `dataMode`, secrets). A model
that starts carrying either is how a boundary dies — one convenient field at a
time.

What this refuses:

  B1  Paperclip work state inside `companies/` or `industries/` — files named
      tickets / runs / checkouts / heartbeats / paperclip.*, or a YAML key
      `tickets`, `runs`, `checkouts`, `heartbeats`, `paperclip_*`. The single
      exception is the compile opt-in block `paperclip: {compile: bool}`, which
      is a declaration about the model, not work state.
  B2  a secret **value** in a model file. Secrets are named by env var
      (`*_env`) or a placeholder (`<...>`, `${...}`, `env:...`); a literal is a
      leak waiting for a commit.
  B3  a company model without a contract pin, or with a pin that is not a
      release tag + 40-hex sha. (Resolution of the tag/sha is
      `validate_company.py`'s job; this is the boundary half.)
  B4  tenant policy re-declared in the model — a YAML key `acl`, `data_mode`,
      `tenant_acl`, `folder_acl`. That file lives in OpenGate, per tenant.

Usage:
  python scripts/check_plane_boundary.py [--root .] [--json]
  python scripts/check_plane_boundary.py --self-test
"""
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ZONES = ("companies", "industries")
STATE_FILES = ("tickets", "runs", "checkouts", "heartbeats", "paperclip")
STATE_KEYS = {"paperclip", "tickets", "runs", "checkouts", "heartbeats"}
TENANT_KEYS = {"acl", "data_mode", "tenant_acl", "folder_acl"}
SECRET_KEY = re.compile(r"^(.*_)?(secret|password|passwd|token|api_key|apikey)$",
                        re.I)
ENV_SUFFIX = re.compile(r"(_env|environment)$", re.I)
PLACEHOLDER = re.compile(r"^(<.*>|\$\{.*\}|env:.+|ENV:.+)$")
TAG = re.compile(r"^contract-\d{4}\.\d{2}\.\d+$")
SHA = re.compile(r"^[0-9a-f]{40}$")


def _docs(root):
    for zone in ZONES:
        base = Path(root) / zone
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix in (".yaml", ".yml", ".json"):
                yield path


def _load(path):
    try:
        if path.suffix == ".json":
            return json.loads(path.read_text())
        return yaml.safe_load(path.read_text())
    except (OSError, ValueError, yaml.YAMLError):
        return None  # another validator reports unparseable files


def _walk(node, path, problems):
    """Yield (key, value, where) for every mapping in the document."""
    if isinstance(node, dict):
        for key, value in node.items():
            name = str(key)
            low = name.lower()
            where = f"{path}: {name}"
            if low == "paperclip":
                if not isinstance(value, dict) or set(value) - {"compile"}:
                    problems.append(f"{where}: only the compile opt-in "
                                    f"`paperclip: {{compile: bool}}` is allowed here "
                                    f"(ADR-002, B1)")
            elif low in STATE_KEYS or low.startswith("paperclip_"):
                problems.append(f"{where}: Paperclip work state does not belong in "
                                f"the model (ADR-002, B1)")
            if low in TENANT_KEYS:
                problems.append(f"{where}: tenant policy belongs in OpenGate, not "
                                f"the model (ADR-002, B4)")
            if SECRET_KEY.match(low) and not ENV_SUFFIX.search(low) \
                    and isinstance(value, str) and value.strip() \
                    and not PLACEHOLDER.match(value.strip()):
                problems.append(f"{where}: secret value in the model — name an env "
                                f"var ({name}_env) instead (ADR-002, B2)")
            yield from _walk(value, path, problems)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item, path, problems)


def check(root=ROOT):
    root = Path(root)
    problems = []
    for path in _docs(root):
        rel = path.relative_to(root).as_posix()
        stem = path.name.split(".")[0].lower()
        if any(stem == name or stem.startswith(name + "-") for name in STATE_FILES):
            problems.append(f"{rel}: Paperclip work state file in the model repo "
                            f"(ADR-002, B1)")
            continue
        if ".schema." in path.name:
            continue  # a schema describes shapes; the boundary rules apply to models
        doc = _load(path)
        for _ in _walk(doc, rel, problems):
            pass
    for company in sorted((root / "companies").glob("*/company.yaml")) \
            if (root / "companies").is_dir() else []:
        rel = company.relative_to(root).as_posix()
        doc = _load(company) or {}
        pin = doc.get("contract") if isinstance(doc, dict) else None
        if not isinstance(pin, dict) or not TAG.match(str(pin.get("tag", ""))) \
                or not SHA.match(str(pin.get("sha", ""))):
            problems.append(f"{rel}: a company model needs contract.tag "
                            f"(contract-YYYY.MM.N) and contract.sha (40 hex) "
                            f"(ADR-002, B3)")
    return problems


def self_test():
    """Prove each rule bites, on a throwaway tree."""
    import tempfile

    failures = []

    def case(label, files, expect):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, text in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            found = check(root)
            ok = (not found) if expect is None else any(expect in p for p in found)
            if not ok:
                failures.append(f"{label}: expected {expect or 'clean'}, got {found}")
            return found

    clean = ("version: 1\nid: acme\ncontract:\n  tag: contract-2026.11.1\n"
             "  sha: " + "a" * 40 + "\n")
    case("clean model", {"companies/acme/company.yaml": clean}, None)
    case("work state file", {"companies/acme/tickets.yaml": "tasks: []\n"}, "B1")
    case("work state key",
         {"companies/acme/company.yaml": clean + "paperclip_sync: true\n"}, "B1")
    case("opt-in block is allowed",
         {"companies/acme/company.yaml": clean + "paperclip:\n  compile: true\n"}, None)
    case("state inside the opt-in block",
         {"companies/acme/company.yaml": clean + "paperclip:\n  tickets: []\n"}, "B1")
    case("schema file describing the block is fine",
         {"companies/acme/company.schema.yaml":
          "paperclip:\n  type: object\n  properties:\n    compile: {type: boolean}\n"},
         None)
    case("secret value",
         {"companies/acme/company.yaml": clean + "db_password: hunter2\n"}, "B2")
    case("secret by env is fine",
         {"companies/acme/company.yaml": clean + "db_password_env: ACME_DB\n"}, None)
    case("tenant acl in model",
         {"industries/x/rules/r.yaml": "acl:\n  hr: [admin]\n"}, "B4")
    case("missing pin", {"companies/acme/company.yaml": "version: 1\nid: acme\n"}, "B3")
    case("bad pin", {"companies/acme/company.yaml":
                     clean.replace("a" * 40, "not-a-sha")}, "B3")
    return failures


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--self-test" in argv:
        failures = self_test()
        if failures:
            print("plane-boundary --self-test RED:")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("plane-boundary --self-test: 11 cases, each rule bites — OK")
        return 0
    root = ROOT
    if "--root" in argv:
        root = Path(argv[argv.index("--root") + 1])
    problems = check(root)
    if "--json" in argv:
        print(json.dumps(problems, indent=1))
    if problems:
        print("PLANE BOUNDARY RED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"plane-boundary: {len(list(_docs(root)))} model files stay in the design "
          f"plane — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
