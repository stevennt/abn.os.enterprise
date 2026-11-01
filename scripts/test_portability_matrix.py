#!/usr/bin/env python3
"""The portability conformance matrix (issue #325).

Every case asserts **which** code fires and **why**, against the implementation
(`scripts/portable.py`), not only against the oracle. The positive cases matter as
much as the negative ones: a checker that refuses everything passes every refusal
test.

    python scripts/test_portability_matrix.py

Exit 0 = green. CI runs it beside the oracle's `--self-test`.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TINY = ROOT / "tests" / "fixtures" / "portability" / "tiny"
FIXTURE_CASE = ROOT / "tests" / "fixtures" / "portability" / "case.valid.json"


def portable():
    spec = importlib.util.spec_from_file_location(
        "portable", ROOT / "scripts" / "portable.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules["portable"] = module
    return module


P = portable()
GOOD_PIN = {"tag": "contract-2026.11.1",
            "sha": "a7baab409dce013bd296b57aafc500565b878dfa"}


def tree(tmp):
    root = Path(tmp) / "repo"
    shutil.copytree(TINY, root)
    return root


def template_path(root):
    return root / "companies" / "acme" / "paperclip-company.json"


def edit_template(root, change):
    path = template_path(root)
    doc = json.loads(path.read_text())
    change(doc)
    path.write_text(json.dumps(doc, indent=2) + "\n")
    return doc


def codes(findings):
    return [code for code, _reason in findings]


CASES = []


def case(label, expected, fragment=""):
    def register(fn):
        CASES.append((label, expected, fragment, fn))
        return fn
    return register


# ---------------------------------------------------------------- refusals
@case("a template with no pin", "E-PORT-02", "contract pin is")
def _(tmp):
    root = tree(tmp)
    edit_template(root, lambda doc: doc.update(contract={}))
    return P.export(root, "acme", platform="contract-2026.11.3")[1]


@case("a pin whose sha is not a commit", "E-PORT-02", "is not a commit")
def _(tmp):
    root = tree(tmp)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.email=t@example.com",
                    "-c", "user.name=T", "commit", "-qm", "seed"], cwd=root,
                   check=True)
    edit_template(root, lambda doc: doc.update(
        contract={"tag": "contract-2026.11.1", "sha": "0" * 40}))
    return P.export(root, "acme", platform="contract-2026.11.3")[1]


@case("a cited file the checkout does not have", "E-PORT-03", "not in this checkout")
def _(tmp):
    root = tree(tmp)
    edit_template(root, lambda doc: doc["source"]["files"].append(
        "companies/acme/missing.yaml"))
    return P.export(root, "acme", platform="contract-2026.11.3")[1]


@case("a cited tenant file", "E-PORT-05", "is tenant data")
def _(tmp):
    root = tree(tmp)
    (root / "customers" / "acme").mkdir(parents=True)
    (root / "customers" / "acme" / "org.json").write_text("{}\n")
    edit_template(root, lambda doc: doc["source"]["files"].append(
        "customers/acme/org.json"))
    return P.export(root, "acme", platform="contract-2026.11.3")[1]


@case("a cited absolute path", "E-PORT-07", "is an absolute path")
def _(tmp):
    root = tree(tmp)
    edit_template(root, lambda doc: doc["source"]["files"].append(
        "/etc/hosts"))
    return P.export(root, "acme", platform="contract-2026.11.3")[1]


@case("a platform older than the pin", "E-PORT-06", "the platform is")
def _(tmp):
    root = tree(tmp)
    return P.export(root, "acme", platform="contract-2026.09.0")[1]


def bundle(tmp, **kwargs):
    root = tree(tmp)
    manifest, findings = P.export(root, "acme", platform="contract-2026.11.3",
                                  **kwargs)
    out = Path(tmp) / "out"
    out.mkdir()
    (out / "bundle.json").write_text(json.dumps(manifest, indent=2) + "\n")
    shutil.copyfile(template_path(root), out / "paperclip-company.json")
    return root, out / "bundle.json", manifest


@case("a manifest that is not JSON", "E-PORT-01", "unreadable")
def _(tmp):
    root, _manifest, _ = bundle(tmp)
    path = Path(tmp) / "out" / "bundle.json"
    path.write_text("{broken")
    try:
        P.verify(root, path)
    except P.PortabilityError as exc:
        return [(exc.code, str(exc))]
    return []


@case("a manifest for another contract", "E-PORT-01", "contract/version")
def _(tmp):
    root, path, _ = bundle(tmp)
    doc = json.loads(path.read_text())
    doc["contract"] = "company-portability@9"
    path.write_text(json.dumps(doc))
    return P.verify(root, path)[1]


@case("a bundle id that does not match its contents", "E-PORT-01", "bundle id")
def _(tmp):
    root, path, _ = bundle(tmp)
    doc = json.loads(path.read_text())
    doc["bundleId"] = "bundle-" + "0" * 16
    path.write_text(json.dumps(doc))
    return P.verify(root, path)[1]


@case("a shipped template whose digest does not match", "E-PORT-04",
      "shipped template")
def _(tmp):
    root, path, _ = bundle(tmp)
    (path.parent / "paperclip-company.json").write_text("{}\n")
    return P.verify(root, path)[1]


@case("a bundle with no template beside it", "E-PORT-03", "beside its manifest")
def _(tmp):
    root, path, _ = bundle(tmp)
    (path.parent / "paperclip-company.json").unlink()
    return P.verify(root, path)[1]


@case("a checkout artefact tampered after export", "E-PORT-04", "the checkout has")
def _(tmp):
    root, path, _ = bundle(tmp)
    flow = next((root / "industries").rglob("*.flow.yaml"))
    flow.write_text(flow.read_text() + "\n# edited\n")
    return P.verify(root, path)[1]


@case("importing over a different compiled model", "E-PORT-04", "different digest")
def _(tmp):
    root, path, _ = bundle(tmp)
    template_path(root).write_text(json.dumps({"version": 9}))
    _manifest, findings, _rel = P.do_import(root, path,
                                            platform="contract-2026.11.3")
    return findings


@case("a rollback that would overwrite without --force", "E-PORT-08",
      "would overwrite")
def _(tmp):
    root, path, _ = bundle(tmp)
    _manifest, findings, _rel = P.do_import(root, path,
                                            platform="contract-2026.11.3")
    _payload, refused = P.record(root, "acme", platform="contract-2026.11.3")
    if refused:
        return refused
    template = template_path(root)
    doc = json.loads(template.read_text())
    doc["label"] = "edited"
    template.write_text(json.dumps(doc, indent=2) + "\n")
    bundle_id = json.loads((root / "companies" / "acme" / "bundles"
                            / "index.jsonl").read_text().splitlines()[0])[
                                "bundleId"]
    _payload, findings = P.rollback(root, "acme", bundle_id)
    return findings


@case("importing a bundle newer than the platform", "E-PORT-06", "this platform")
def _(tmp):
    root, path, _ = bundle(tmp)
    _manifest, findings, _rel = P.do_import(root, path,
                                            platform="contract-2026.09.0")
    return findings


# ---------------------------------------------------------------- positives
@case("a clean export", None)
def _(tmp):
    root = tree(tmp)
    return P.export(root, "acme", platform="contract-2026.11.3")[1]


@case("two exports of one state share an id", None)
def _(tmp):
    root = tree(tmp)
    first = P.export(root, "acme", platform="contract-2026.11.3")[0]
    second = P.export(root, "acme", platform="contract-2026.11.3")[0]
    return [] if first["bundleId"] == second["bundleId"] else \
        [("E-PORT-01", "the ids differ")]


@case("a newer platform accepts an older bundle", None)
def _(tmp):
    root, path, _ = bundle(tmp)
    _manifest, findings, rel = P.do_import(root, path,
                                           platform="contract-2026.12.0")
    return findings if rel is None else []


@case("the oracle's own bundle id", None)
def _(tmp):
    case = json.loads(FIXTURE_CASE.read_text())
    expected = case["expected"]["manifest"]["bundleId"]
    mine = P.bundle_id(case["company"], case["template"]["sha256"],
                       case["artefacts"])
    return [] if mine == expected else [("E-PORT-01", f"{mine} != {expected}")]


def main():
    failures = []
    seen = set()
    for label, expected, fragment, fn in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                findings = fn(tmp)
            except Exception as exc:  # noqa: BLE001 - a case that crashes is red
                failures.append(f"{label}: raised {type(exc).__name__}: {exc}")
                continue
        found = codes(findings)
        if expected is None:
            if findings:
                failures.append(f"{label}: expected no finding, got {findings}")
            continue
        seen.add(expected)
        if expected not in found:
            failures.append(f"{label}: wanted {expected}, got {found or 'nothing'}")
            continue
        reason = next(reason for code, reason in findings if code == expected)
        if fragment and fragment not in reason:
            failures.append(f"{label}: {expected} fired for the wrong reason: "
                            f"{reason!r}")
    every = set(P.CODES)
    if seen != every:
        failures.append(f"the matrix does not cover {sorted(every - seen)}")
    if failures:
        print("portability matrix RED:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    positives = sum(1 for _label, expected, _fragment, _fn in CASES
                    if expected is None)
    print(f"portability matrix: {len(CASES)} cases — {len(seen)} refusals, each "
          f"for its own reason, and {positives} positive — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
