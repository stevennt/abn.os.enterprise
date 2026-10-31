#!/usr/bin/env python3
"""BPMN exporter (issue #107): every examples/bank/*.flow.yaml -> build/bpmn/*.bpmn.
Linear chain: start -> serviceTask per step (type bank-<step-id>) -> end.
Human steps keep kind in the task name (engine truth stays in YAML).
Round-trip: re-parse exported XML, assert step-id sequence == flow steps.
Usage: python scripts/export_bpmn.py [--check]  (--check only verifies, writes nothing)
"""
import glob, re, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "bpmn"

def to_bpmn(flow):
    pid = flow["id"]
    parts = [f'<bpmn:process id="{pid}" name="{pid}" isExecutable="true">']
    parts.append('<bpmn:startEvent id="start" />')
    for s in flow["steps"]:
        parts.append(
            f'<bpmn:serviceTask id="{s["id"]}" name="{s["id"]} [{s["kind"]}]">'
            f'<bpmn:extensionElements><zeebe:taskDefinition type="bank-{s["id"]}" />'
            f"</bpmn:extensionElements></bpmn:serviceTask>")
    parts.append('<bpmn:endEvent id="end" />')
    seq = []
    ids = ["start"] + [s["id"] for s in flow["steps"]] + ["end"]
    for a, b in zip(ids, ids[1:]):
        seq.append(f'<bpmn:sequenceFlow id="f-{a}-to-{b}" sourceRef="{a}" targetRef="{b}" />')
    head = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
            'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
            f'id="{pid}-defs" targetNamespace="http://abnasia.org/os">\n')
    return head + "\n".join(parts) + "\n" + "\n".join(seq) + "\n</bpmn:process>\n</bpmn:definitions>\n"

def roundtrip(xml, flow):
    got = re.findall(r'<bpmn:serviceTask id="([^"]+)"', xml)
    want = [s["id"] for s in flow["steps"]]
    assert got == want, f"lost steps: {want} vs {got}"
    return True

def main():
    check = "--check" in sys.argv
    files = sorted(glob.glob(str(ROOT / "examples" / "bank" / "*.flow.yaml")))
    assert len(files) == 15, f"want 15 flows, found {len(files)}"
    if not check:
        OUT.mkdir(parents=True, exist_ok=True)
    for f in files:
        flow = yaml.safe_load(open(f))
        xml = to_bpmn(flow)
        roundtrip(xml, flow)
        if not check:
            (OUT / (Path(f).stem.replace(".flow", "") + ".bpmn")).write_text(xml)
    print(f"bpmn: {len(files)} flows exported + round-tripped — OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
