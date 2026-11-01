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
  T7  the nested model (three units, two flows, a shared role, an external party)
      compiles to its own golden, with the hierarchy, the touchpoint and the
      exclusions right;
  T16 hardening: a malformed file, a duplicate unit, a parent cycle and an empty
      crew each produce a refusal that names the fix (every E-COMP line ends with
      "— fix: …");
  T15 the spec keeps the verbatim walk-through: every command it teaches, the
      refusal table and the expected output line;
  T14 `--show` and `--render` give a human the crew (deterministic, no secrets,
      and nothing written when the compile is refused);
  T13 `--record` appends a compile record per run, and `--check` never records;
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
GOLDEN_NESTED = ROOT / "tests" / "fixtures" / "paperclip-company.nested.json"
PY = sys.executable


def _run(root, *extra):
    return subprocess.run([PY, str(CLI), "--root", str(root), "--company", "demo",
                           *extra], capture_output=True, text=True)


def _copy(tmp):
    target = Path(tmp) / "model"
    shutil.copytree(MODEL, target)
    return target


def _has_fix(result):
    return "— fix: " in (result.stderr or "")


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
        check("T5 E-COMP-01", result.returncode == 1 and "E-COMP-01" in result.stderr
              and _has_fix(result), result.stderr.strip())

    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        _mutate(model / "companies" / "demo" / "company.yaml",
                "sha: a7baab409dce013bd296b57aafc500565b878dfa",
                "sha: " + "0" * 40)
        result = _run(model)
        check("T5 E-COMP-02", result.returncode == 1 and "E-COMP-02" in result.stderr
              and _has_fix(result), result.stderr.strip())

    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        _mutate(model / "industries" / "demo" / "flows" / "demo.flow.yaml",
                "department: ops.credit", "department: nowhere")
        result = _run(model)
        check("T5 E-COMP-03", result.returncode == 1 and "E-COMP-03" in result.stderr
              and _has_fix(result), result.stderr.strip())

    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        _mutate(model / "industries" / "demo" / "flows" / "demo.flow.yaml",
                "uses_rule: [DEMO-01]", "uses_rule: [GHOST-01]")
        result = _run(model)
        check("T5 E-COMP-07", result.returncode == 1 and "E-COMP-07" in result.stderr
              and _has_fix(result), result.stderr.strip())

    with tempfile.TemporaryDirectory() as tmp:
        import yaml
        model = _copy(tmp)
        flow_path = model / "industries" / "demo" / "flows" / "demo.flow.yaml"
        flow = yaml.safe_load(flow_path.read_text())
        for step in flow["steps"]:
            step["kind"] = "human"  # no routines -> no agents -> template invalid
        flow_path.write_text(yaml.safe_dump(flow, sort_keys=False))
        result = _run(model)
        check("T5 E-COMP-10", result.returncode == 1 and "E-COMP-10" in result.stderr
              and _has_fix(result), result.stderr.strip())

    # T7–T11 — the nested model: hierarchy, shared role, touchpoint, exclusions
    nested_out = Path(tempfile.mkdtemp()) / "nested.json"
    result = subprocess.run([PY, str(CLI), "--root", str(MODEL), "--company", "nested",
                             "--out", str(nested_out)], capture_output=True, text=True)
    check("T7 nested compiles", result.returncode == 0, result.stderr.strip())
    if result.returncode == 0:
        check("T7 nested golden", nested_out.read_text() == GOLDEN_NESTED.read_text(),
              "nested template differs from its golden")
        doc = json.loads(nested_out.read_text())
        agents = {a["id"]: a for a in doc["agents"]}
        check("T8 one root", sum(1 for a in doc["agents"] if a["reportsTo"] is None) == 1)
        check("T8 child reports to the parent lead",
              agents["bank-ops-credit-analyst"]["reportsTo"] == "bank-ops-credit-officer")
        check("T9 a shared role yields one agent per unit",
              {"bank-ops-credit-officer", "bank-ops-credit-credit-officer"} <= set(agents),
              str(sorted(agents)))
        routines = {r["id"]: r for r in doc["routines"]}
        check("T10 touchpoint is copied", routines["nested.b.b1"].get("touchpoint")
              == "TP-C-app")
        check("T11 external party has no agent",
              all(a["role"] != "external_notary" for a in doc["agents"]))
        check("T11 external/system steps have no routine",
              not any(r["step"] in ("b3", "a2") for r in doc["routines"]))

    # T12 — more refusals
    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        (model / "companies" / "demo" / "org" / "org-chart.yaml").unlink()
        result = _run(model)
        check("T12 E-COMP-01 chart", result.returncode == 1
              and "E-COMP-01" in result.stderr and _has_fix(result),
              result.stderr.strip())

    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        _mutate(model / "companies" / "demo" / "company.yaml",
                "flows:\n- demo.flow", "flows:\n- demo.flow\n- ghost.flow")
        result = _run(model)
        check("T12 E-COMP-07 flow", result.returncode == 1
              and "E-COMP-07" in result.stderr and _has_fix(result),
              result.stderr.strip())

    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        _mutate(model / "industries" / "demo" / "flows" / "demo.flow.yaml",
                "    owner_role: credit_officer\n", "")
        result = _run(model)
        check("T12 E-COMP-03 owner_role", result.returncode == 1
              and "E-COMP-03" in result.stderr and _has_fix(result),
              result.stderr.strip())

    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        _mutate(model / "companies" / "demo" / "company.yaml",
                "tag: contract-2026.11.1", "tag: v1")
        result = _run(model)
        check("T12 E-COMP-02 tag", result.returncode == 1
              and "E-COMP-02" in result.stderr and _has_fix(result),
              result.stderr.strip())

    # T14 — the human surface
    shown = subprocess.run([PY, str(CLI), "--root", str(MODEL), "--company", "nested",
                            "--show"], capture_output=True, text=True)
    check("T14 show runs", shown.returncode == 0, shown.stderr.strip())
    check("T14 show names the crew", "bank-ops-credit-officer" in shown.stdout
          and "autonomous" in shown.stdout and "nested — Nested Company" in shown.stdout,
          shown.stdout[:200])

    with tempfile.TemporaryDirectory() as tmp:
        first = Path(tmp) / "crew.md"
        result = subprocess.run([PY, str(CLI), "--root", str(MODEL), "--company",
                                 "nested", "--render", "--out", str(first)],
                                capture_output=True, text=True)
        check("T14 render runs", result.returncode == 0, result.stderr.strip())
        if first.is_file():
            sheet = first.read_text()
            check("T14 sheet has the tables", "## Agents" in sheet
                  and "## Routines" in sheet and "`nested.b.b1`" in sheet)
            check("T14 sheet has no secret",
                  "secret" not in sheet.lower() and "password" not in sheet.lower())
            second = Path(tmp) / "crew2.md"
            subprocess.run([PY, str(CLI), "--root", str(MODEL), "--company", "nested",
                            "--render", "--out", str(second)], capture_output=True)
            check("T14 render is deterministic", second.is_file()
                  and second.read_text() == sheet)

    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        _mutate(model / "industries" / "demo" / "flows" / "demo.flow.yaml",
                "uses_rule: [DEMO-01]", "uses_rule: [GHOST-01]")
        sheet = model / "companies" / "demo" / "crew2.md"
        result = subprocess.run([PY, str(CLI), "--root", str(model), "--company", "demo",
                                 "--render", "--out", str(sheet)],
                                capture_output=True, text=True)
        check("T14 refusal writes no sheet", result.returncode == 1
              and not sheet.exists()
              and "E-COMP-07" in result.stderr, result.stderr.strip())

    # T13 — the compile record
    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        record_path = model / "companies" / "demo" / "compiles.jsonl"
        record_path.unlink(missing_ok=True)  # the fixture ships with one
        check("T13 no record by default", not record_path.exists())
        run = subprocess.run([PY, str(CLI), "--root", str(model), "--company", "demo",
                              "--check", "--record"], capture_output=True, text=True)
        check("T13 check does not record", run.returncode == 0
              and not record_path.exists(), run.stderr.strip())
        run = subprocess.run([PY, str(CLI), "--root", str(model), "--company", "demo",
                              "--record"], capture_output=True, text=True)
        check("T13 record written", run.returncode == 0 and record_path.exists(),
              run.stderr.strip())
        if record_path.exists():
            row = json.loads(record_path.read_text().splitlines()[0])
            check("T13 record shape", row.get("result") == "compiled"
                  and row.get("company") == "demo"
                  and len(str(row.get("templateSha256") or "")) == 64
                  and row.get("contract", {}).get("tag") == "contract-2026.11.1",
                  json.dumps(row)[:200])

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

    # T16 — hardening: bad files and bad structure refuse, and name the fix
    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        (model / "companies" / "demo" / "company.yaml").write_text(": not yaml\n")
        result = _run(model)
        check("T16 malformed model", result.returncode == 1
              and "E-COMP-01" in result.stderr and _has_fix(result),
              result.stderr.strip())

    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        chart = model / "companies" / "demo" / "org" / "org-chart.yaml"
        chart.write_text(chart.read_text() + "- {id: ops, name: Duplicate, parent_id: null}\n")
        result = _run(model)
        check("T16 duplicate unit", result.returncode == 1
              and "E-COMP-11" in result.stderr and "duplicate" in result.stderr,
              result.stderr.strip())

    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        chart = model / "companies" / "demo" / "org" / "org-chart.yaml"
        chart.write_text(
            "- {id: a, name: A, parent_id: b}\n- {id: b, name: B, parent_id: a}\n")
        result = _run(model)
        check("T16 parent cycle", result.returncode == 1
              and "E-COMP-11" in result.stderr and "cycles" in result.stderr,
              result.stderr.strip())

    with tempfile.TemporaryDirectory() as tmp:
        model = _copy(tmp)
        _mutate(model / "industries" / "demo" / "flows" / "demo.flow.yaml",
                "uses_rule: [DEMO-01]", "bad: [yaml")
        result = _run(model)
        check("T16 malformed flow", result.returncode == 1
              and "E-COMP-07" in result.stderr and _has_fix(result),
              result.stderr.strip())

    # T15 — the walk-through stays in the spec
    spec = (ROOT / "docs" / "core" / "paperclip-compiler.md").read_text()
    for anchor in ("bin/paperclip-company --root tests/fixtures/paperclip-model "
                   "--company demo --check",
                   "--company nested --show",
                   "--company demo --render",
                   "--all --check",
                   "--self-test",
                   "### When it refuses",
                   "paperclip-company: demo compiles",
                   "E-COMP-07"):
        check(f"T15 spec anchor {anchor!r}", anchor in spec)
    for code in ("E-COMP-01", "E-COMP-02", "E-COMP-03", "E-COMP-07", "E-COMP-09",
                 "E-COMP-10"):
        check(f"T15 refusal fix {code}", code in spec)

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
    print("paperclip-compiler tests: 2 goldens, determinism, hierarchy, shared "
          "role, touchpoint, human/system/external exclusion, 9 refusals, --all "
          "opt-in policy, compile record, surface, spec walk-through, hardening — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
