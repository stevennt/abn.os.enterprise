#!/usr/bin/env python3
"""Secret references: the oracle for `secret-ref@1` (issue #412).

The schema (`schemas/secret-ref.json`) says what a run env manifest looks like.
This script checks what a schema cannot: that every `env` value is a `vault://`
reference and not a value, that every name is a POSIX environment name, that every
`required` name is declared — and that the **resolution** refuses, with a code, when
a value is missing, empty, or asked to be recorded.

Usage:
    python scripts/check_secret_ref_spec.py [path]
    python scripts/check_secret_ref_spec.py --self-test
    python scripts/check_secret_ref_spec.py --json [path]

Exit 0 = green. `--self-test` takes the valid fixture and breaks it eight ways — one
per code — and fails if a code does not appear with its fix. That is what CI runs.

This file is also the specification of the resolution: when OpenGate implements it
(#413), every refusal below is the behaviour the implementation must match.
"""
import argparse
import copy
import json
import re
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "secret-ref.json"
FIXTURE = ROOT / "tests" / "fixtures" / "secrets" / "env.valid.json"

NAME = re.compile(r"^[A-Z_][A-Z0-9_]*$")
REFERENCE = re.compile(r"^vault://([A-Za-z0-9][A-Za-z0-9._/-]*)#([A-Za-z0-9][A-Za-z0-9._-]*)$")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")

CODES = {
    "E-SEC-01": "a value where a reference belongs — move the value to the vault and "
                "put its reference in the manifest",
    "E-SEC-02": "a malformed reference — write vault://<file>#<key>",
    "E-SEC-03": "the name is not in the adapter's environment — inject it from the "
                "vault at deploy",
    "E-SEC-04": "the variable exists but is empty — an empty secret is a missing "
                "secret",
    "E-SEC-05": "a name that is not a POSIX environment name — rename it",
    "E-SEC-06": "a required name is not declared — declare it, or stop requiring it",
    "E-SEC-07": "the manifest is missing or unreadable — a run with no env manifest "
                "does not start",
    "E-SEC-08": "a resolution line tried to carry a value — record the name, the "
                "reference and the outcome",
}


def problem(code, message):
    return {"code": code, "message": str(message), "fix": CODES[code]}


# --------------------------------------------------------------------- the manifest
def shape_problems(document):
    schema = json.loads(SCHEMA.read_text())
    validator = jsonschema.Draft7Validator(schema)
    out = []
    for error in sorted(validator.iter_errors(document), key=lambda e: list(e.path)):
        out.append(problem("E-SEC-02",
                           f"{'/'.join(str(part) for part in error.path) or 'manifest'}: "
                           f"{error.message}"))
    return out


def reference_problems(document):
    """The rules a JSON Schema cannot express, or expresses too vaguely."""
    out = []
    env = document.get("env")
    if not isinstance(env, dict):
        return [problem("E-SEC-02", "env must be an object of name → reference")]
    for name, value in sorted(env.items()):
        if not NAME.match(str(name)):
            out.append(problem("E-SEC-05", f"{name!r} is not a POSIX environment name"))
        text = str(value or "")
        if not text.startswith("vault://"):
            if SCHEME.match(text):
                out.append(problem("E-SEC-02",
                                   f"{name} reference {text!r} does not use the "
                                   f"vault:// scheme"))
            else:
                # the headline rule: a value where a reference belongs
                out.append(problem("E-SEC-01",
                                   f"{name} carries a value, not a reference"))
            continue
        match = REFERENCE.match(text)
        if not match:
            out.append(problem("E-SEC-02",
                               f"{name} reference {text!r} is not vault://<file>#<key>"))
            continue
        path, key = match.group(1), match.group(2)
        if path.startswith("/") or ".." in path.split("/") or key.endswith("."):
            out.append(problem("E-SEC-02",
                               f"{name} reference {text!r} names a path outside the "
                               f"vault or an empty key"))
    declared = {str(name) for name in env}
    for name in document.get("required") or []:
        if str(name) not in declared:
            out.append(problem("E-SEC-06",
                               f"{name} is required but not declared in env"))
    return out


def load(path):
    try:
        document = json.loads(Path(path).read_text())
    except FileNotFoundError:
        return None, [problem("E-SEC-07", f"{path} does not exist")]
    except (OSError, ValueError) as exc:
        return None, [problem("E-SEC-07", f"{path} cannot be read ({exc})")]
    return document, []


def check(path):
    document, out = load(path)
    if document is None:
        return out
    out.extend(shape_problems(document))
    out.extend(reference_problems(document))
    return out


# ---------------------------------------------------------------------- resolution
def resolve(document, environ):
    """(resolved, problems) — the values, and every reason a run must not start.

    This is the behaviour OpenGate implements (#413): a name is read from the
    process environment, an absent or empty value stops the run, and nothing here
    returns a value in a problem, a log line or a record.
    """
    resolved, out = {}, []
    for name, reference in sorted((document.get("env") or {}).items()):
        value = environ.get(name)
        if value is None:
            out.append(problem("E-SEC-03", f"{name} is not set for this process"))
            continue
        if not str(value).strip():
            out.append(problem("E-SEC-04", f"{name} is set but empty"))
            continue
        resolved[name] = value
    return resolved, out


def record_line(document, name, reference, value=None, code=None, at=None):
    """The line a resolution leaves behind — and the refusal if it carries a value."""
    if value is not None and str(value).strip():
        # a value, or even a readable prefix of one, is the copy this contract exists
        # to prevent: the record names the secret, never any part of it
        raise ValueError(
            f"E-SEC-08: a resolution line for {name} tried to carry a value — "
            f"fix: {CODES['E-SEC-08']}")
    line = {"version": 1, "at": at or "2026-11-03T09:00:00Z", "runId": document["runId"],
            "name": name, "ref": reference, "ok": code is None}
    if code:
        line["code"] = code
    return line


# ------------------------------------------------------------------- the self-test
def self_test():
    valid = json.loads(FIXTURE.read_text())
    cases = []

    def case(code, mutate, environ=None, resolve_after=False):
        document = copy.deepcopy(valid)
        mutate(document)
        if resolve_after:
            found = resolve(document, environ or {})[1]
        else:
            found = check_document(document)
        return code, [item["code"] for item in found], found

    def check_document(document):
        return shape_problems(document) + reference_problems(document)

    def a_value(document):
        document["env"]["KIMI_API_KEY"] = "sk-live-8f2b9c"

    def a_bad_reference(document):
        document["env"]["KIMI_API_KEY"] = "env://KIMI_API_KEY"

    def a_bad_name(document):
        document["env"]["kimi-key"] = "vault://os/prod.enc.yaml#providers.kimi.key"
        del document["env"]["KIMI_API_KEY"]

    def a_missing_required(document):
        document["required"].append("DATABASE_URL")

    def a_path_outside(document):
        document["env"]["KIMI_API_KEY"] = "vault://../etc/passwd#key"

    cases.append(case("E-SEC-01", a_value))
    cases.append(case("E-SEC-02", a_bad_reference))
    cases.append(case("E-SEC-02", a_path_outside))
    cases.append(case("E-SEC-05", a_bad_name))
    cases.append(case("E-SEC-06", a_missing_required))
    cases.append(case("E-SEC-03", lambda document: None, environ={}, resolve_after=True))
    cases.append(case("E-SEC-04", lambda document: None,
                      environ={name: "  " for name in valid["env"]},
                      resolve_after=True))
    missing = check(ROOT / "tests" / "fixtures" / "secrets" / "does-not-exist.json")
    if not missing or missing[0]["code"] != "E-SEC-07":
        failures_missing = "E-SEC-07 did not appear for a missing manifest"
    else:
        failures_missing = None
    if failures_missing:
        print("secret-ref self-test RED:", file=sys.stderr)
        print(f"  - {failures_missing}", file=sys.stderr)
        return 1

    line_ok = True
    try:
        record_line(valid, "KIMI_API_KEY", valid["env"]["KIMI_API_KEY"],
                    value="sk-live-8f2b9c")
        line_ok = False
    except ValueError as exc:
        line_ok = "E-SEC-08" in str(exc) and "fix: " in str(exc)

    failures = []
    for code, found, problems in cases:
        if code not in found:
            failures.append(f"{code} did not appear (found {found or 'nothing'})")
        for item in problems:
            if not item["fix"]:
                failures.append(f"{code} appeared without a fix")
    if not line_ok:
        failures.append("E-SEC-08: the recorder accepted a value")

    # the valid fixture must be clean, and a full environment must resolve
    clean = check(FIXTURE)
    if clean:
        failures.append(f"the valid fixture is not clean: "
                        f"{[item['code'] for item in clean]}")
    resolved, found = resolve(valid, {name: "x" for name in valid["env"]})
    if found or set(resolved) != set(valid["env"]):
        failures.append(f"a full environment did not resolve: {[i['code'] for i in found]}")

    if failures:
        print("secret-ref self-test RED:", file=sys.stderr)
        for line in failures:
            print(f"  - {line}", file=sys.stderr)
        return 1
    seen = sorted({code for code, _found, _problems in cases} | {"E-SEC-07", "E-SEC-08"})
    print(f"secret-ref self-test: {len(cases) + 2} mutations, "
          f"{', '.join(seen)} refused with their fix — OK")
    return 0


# ---------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(prog="check_secret_ref_spec.py")
    ap.add_argument("path", nargs="?", default=str(FIXTURE))
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    problems = check(args.path)
    if args.json:
        print(json.dumps({"ok": not problems, "problems": problems}, indent=2,
                         ensure_ascii=False))
    else:
        for item in problems:
            print(f"{item['code']}: {item['message']} — fix: {item['fix']}")
        if not problems:
            print(f"secret-ref: {Path(args.path).name} is references only — OK")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
