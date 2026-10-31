# Decision explainer v1.0 (issue #86) — every decision in human words

Generated from the audit chain (E49), never hand-written: inputs + rule versions +
actor chain rendered through templates below. VI default, EN on request.

## Template

```
[Quyết định] {APPROVE/DECLINE/REVIEW} hồ sơ {ref} lúc {ts}.
[Lý do chính] {top reason in plain words} ({rule_id}@{version}).
[Lý do phụ] {up to 2 more, same format}.
[Người/quy trình] {actor chain: system steps + human approver + model versions}.
[Bước tiếp theo] {appeal ETA / disbursal ETA / what customer should do}.
```

## Worked examples

1. Decline: "Hồ sơ APP-104231 chưa được duyệt lúc 14:02 12/11. Lý do chính: tỷ lệ
   trả nợ trên thu nhập 0.68 vượt mức 0.60 (SBV-DSTI-04@2026-10-01). Lý do phụ:
   thu nhập chưa xác minh đầy đủ. Hồ sơ do hệ thống chấm và credit_manager duyệt.
   Anh/chị có thể bổ sung sao kê 3 tháng để thẩm định lại."
2. Approve: "Hồ sơ APP-104232 được duyệt hạn mức 300.000.000 VND lúc 09:15 12/11
   (CREDIT-GRID-11@2026-10-01). Bước tiếp theo: ký điện tử trong 72h để giải ngân."
3. REVIEW: "Hồ sơ APP-104233 đang chờ thẩm định bổ sung (dự kiến trong 24h):
   giấy tờ tùy thân cần xác minh lại (KYC-01@2026-10-01)."

Rules: numbers always from cited inputs (G64 grounding); no codes without words;
auditor variant appends full version pins + hashes.
