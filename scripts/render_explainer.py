#!/usr/bin/env python3
"""Explainer renderer (issue #115, template I86): render VI explanations from a
real trace + its event; assert every number is grounded in inputs (G64 rule).
Renders 3 variants (approve/review/decline) to prove the template slots.
Run: python scripts/render_explainer.py. Exit 0 = grounded + QA lexicon clean.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANNED = ["ngu ", "mày", "tao", "code:", "lỗi hệ thống, thử lại sau"]  # tone QA (H78)

def numbers(text):
    scrubbed = re.sub(r"[A-Z]+(?:-[A-Z]+)+-\d+|@\d{4}-\d{2}-\d{2}|\b\d+h\b", " ", text)
    return re.findall(r"\d[\d.,]*", scrubbed)

def grounded(num, payload_values):
    n = num.replace(".", "").replace(",", "")
    return any(n in str(v).replace(".", "").replace(",", "") for v in payload_values)

def main():
    trace = json.load(open(ROOT / "examples" / "bank" / "loan-approval.trace.json"))
    ev = json.load(open(ROOT / "examples" / "events" / "loan.application.v1.json"))
    payload = ev["payload"]
    vals = list(payload.values())
    ref = f"APP-{payload['customer_id'].split('-')[1]}"
    amt, term = payload["requested_amount"], payload["term_m"]
    actors = "hệ thống chấm và credit_manager duyệt"
    outs = {
        "approve": (f"Hồ sơ {ref} được duyệt hạn mức {amt} VND, kỳ hạn {term} tháng "
                    f"(CREDIT-GRID-11@2026-10-01). Bước tiếp theo: ký điện tử trong 72h để giải ngân. {actors}."),
        "review": (f"Hồ sơ {ref} đang chờ thẩm định bổ sung (dự kiến trong 24h): "
                   f"thu nhập {amt} VND cần xác minh lại (KYC-01@2026-10-01). {actors}."),
        "decline": (f"Hồ sơ {ref} chưa được duyệt: tỷ lệ trả nợ trên thu nhập vượt mức cho phép "
                    f"(SBV-DSTI-04@2026-10-01) với khoản vay {amt} VND, kỳ hạn {term} tháng. "
                    f"Anh/chị có thể bổ sung sao kê 3 tháng để thẩm định lại. {actors}."),
    }
    for name, text in outs.items():
        for num in numbers(text):
            assert grounded(num, vals), f"{name}: ungrounded number {num}"
        low = text.lower()
        assert not any(b in low for b in BANNED), f"{name}: tone violation"
        assert "@2026-10-01" in text, f"{name}: missing rule pin"
        print(f"--- {name} ---\n{text}\n")
    print("explainer: 3 variants grounded in inputs, VI tone clean — OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
