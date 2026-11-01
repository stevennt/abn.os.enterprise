#!/usr/bin/env python3
"""Tests for the company compiler (issue #253).

The compiler is `bin/paperclip-company`; its spec is
`docs/core/paperclip-compiler.md`. These tests are the acceptance it has to
satisfy, and they fail if a behaviour is removed:

  T1  the fixture model compiles to the committed golden template, byte for byte;
  T2  compiling twice produces the same bytes (determinism);
  T3  a step backed by a `pending-*` rule is compiled **supervised** — if the
      autonomy ceiling is dropped, T1 and T3 both go red;
  T4  human steps and the `system` role produce no routine;
  T6  `--all` compiles every opted-in company and fails only for those: a refused
      company that opted in fails the run, a refused company that did not is
      reported and skipped;
  T5  the refusals fire with their codes: no company.yaml (E-COMP-01), a pin that
      does not resolve (E-COMP-02), a department with no unit (E-COMP-03), an
      unknown rule (E-COMP-07), a template that fails the checker (E-COMP-10).

Usage: python scripts/test_paperclip_company.py [--json]
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "bin" / "paperclip-company"
MODEL = ROOT / "tests" / "fixtures" / "paperclip-model"
GOLDEN = ROOT / "tests" / "fixtures" / "paperclip-company.demo.json"
PY = sys.executable


def _run(root, *extra):
    return subprocess.run([PY, str(CLI), "--root", str(root), "--company", "demo",
                           *extra], capture_output=True, text=True)


def _copy(tmp):
    target = Path(tmp) / "model"
    shutil.copytree(MODEL, target)
    return target


def _mutate(path, old, new):
    text = path.read_text()
    assert old in text, f"fixture drift: {old!r} not in {path}"
    path.write_text(text.replace(old, new, 1))


def tests():
    failures = []

    def check(label, condition, detail=""):
        if not condition:
            failures.append(f"{label}{(': ' + detail) if detail else ''}")

    # T1 — golden
    out = Path(tempfile.mkdtemp()) / "t.json"
    result = _run(MODEL, "--out", str(out))
    check("T1 compile", result.returncode == 0, result.stderr.strip())
    if result.returncode == 0:
        check("T1 golden", out.read_text() == GOLDEN.read_text(),
              "compiled template differs from the golden fixture")

    # T2 — determinism
    second = Path(tempfile.mkdtemp()) / "t.json"
    _run(MODEL, "--out", str(second))
    check("T2 deterministic",
          out.is_file() and second.is_file() and out.read_text() == second.read_text())

    # T3/T4 — semantics on the compiled template
    if out.is_file():
        doc = json.loads(out.read_text())
        pending = [r for r in doc["routines"] if r["ruleStatus"] == "pending"]
        check("T3 pending rule exists", bool(pending), "fixture should have one")
        check("T3 pending stays supervised",
              all(r["autonomy"] == "supervised" for r in pending))
        check("T3 L2 never autonomous",
              all(r["autonomy"] == "supervised" for r in doc["routines"]
                  if r["level"] == "L2"))
        steps = {r["step"] for r in doc["routines"]}
        check("T4 human step has no routine", "s3-approve" not in steps, str(steps))
        check("T4 system step has no routine", "s4-notify" not in steps, str(steps))
        check("T4 no agent for the system role",
              all(a["role"] != "system" for a in doc["agents"]))

    # T5 — refusals
    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        (model / "companies" / "demo" / "company.yaml").unlink()
        result = _run(model)
        check("T5 E-COMP-01", result.returncode == 1 and "E-COMP-01" in result.stderr,
              result.stderr.strip())

    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        _mutate(model / "companies" / "demo" / "company.yaml",
                "sha: a7baab409dce013bd296b57aafc500565b878dfa",
                "sha: " + "0" * 40)
        result = _run(model)
        check("T5 E-COMP-02", result.returncode == 1 and "E-COMP-02" in result.stderr,
              result.stderr.strip())

    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        _mutate(model / "industries" / "demo" / "flows" / "demo.flow.yaml",
                "department: ops.credit", "department: nowhere")
        result = _run(model)
        check("T5 E-COMP-03", result.returncode == 1 and "E-COMP-03" in result.stderr,
              result.stderr.strip())

    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        _mutate(model / "industries" / "demo" / "flows" / "demo.flow.yaml",
                "uses_rule: [DEMO-01]", "uses_rule: [GHOST-01]")
        result = _run(model)
        check("T5 E-COMP-07", result.returncode == 1 and "E-COMP-07" in result.stderr,
              result.stderr.strip())

    with tempfile.TemporaryDirectory() as tmp:
        import yaml
        model = _copy(tmp)
        flow_path = model / "industries" / "demo" / "flows" / "demo.flow.yaml"
        flow = yaml.safe_load(flow_path.read_text())
        for step in flow["steps"]:
            step["kind"] = "human"  # no routines -> no agents -> template invalid
        flow_path.write_text(yaml.safe_dump(flow, sort_keys=False))
        result = _run(model)
        check("T5 E-COMP-10", result.returncode == 1 and "E-COMP-10" in result.stderr,
              result.stderr.strip())

    # T6 — the --all policy (opt-in decides whether a refusal fails the build)
    with tempfile.TemporaryDirectory() as tmp:
        import yaml
        model = _copy(tmp)
        source = model / "companies" / "demo"
        broken = model / "companies" / "broken"
        shutil.copytree(source, broken)
        company = yaml.safe_load((broken / "company.yaml").read_text())
        company["id"] = "broken"
        (broken / "company.yaml").write_text(yaml.safe_dump(company, sort_keys=False))
        flow_path = model / "industries" / "demo" / "flows" / "demo.flow.yaml"
        flow = yaml.safe_load(flow_path.read_text())
        flow["id"] = "broken.flow"
        for step in flow["steps"]:
            step["uses_rule"] = ["GHOST-01"]
        (model / "industries" / "demo" / "flows" / "broken.flow.yaml").write_text(
            yaml.safe_dump(flow, sort_keys=False))
        company["flows"] = ["broken.flow"]
        (broken / "company.yaml").write_text(yaml.safe_dump(company, sort_keys=False))

        all_run = subprocess.run([PY, str(CLI), "--root", str(model), "--all", "--check"],
                                 capture_output=True, text=True)
        check("T6 opted-in refusal fails", all_run.returncode == 1,
              all_run.stdout + all_run.stderr)
        check("T6 reports both", "demo: compiled" in all_run.stdout
              and "broken: FAIL" in all_run.stdout, all_run.stdout)

        company["paperclip"] = {"compile": False}
        (broken / "company.yaml").write_text(yaml.safe_dump(company, sort_keys=False))
        all_run = subprocess.run([PY, str(CLI), "--root", str(model), "--all", "--check"],
                                 capture_output=True, text=True)
        check("T6 non-opted refusal is skipped", all_run.returncode == 0,
              all_run.stdout + all_run.stderr)
        check("T6 skip is labelled", "broken: skip" in all_run.stdout, all_run.stdout)

    return failures


def main():
    failures = tests()
    if "--json" in sys.argv:
        print(json.dumps(failures, indent=1))
    if failures:
        print("PAPERCLIP COMPILER TESTS RED:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("paperclip-compiler tests: golden, determinism, autonomy ceiling, "
          "human/system exclusion, 5 refusals, --all opt-in policy — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
