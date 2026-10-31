---
name: legal-charge-determination
version: "1.0.0"
description: Xác định tội danh theo cấu thành tội phạm bốn yếu tố, đối chiếu điều luật và khung hình phạt, loại trừ tội danh cạnh tranh.
license: Proprietary
compatibility: opencode
metadata:
  domain: legal
  qc_id: QC-LEGAL-004
---

# Xác định tội danh

Product source: `industries/legal/pack/skills/legal-charge-determination/`. Active only when the legal industry pack is pinned and enabled. Bổ trợ cho `legal-issue-spotting`: skill này đi sâu một việc —
từ chứng cứ đi đến tội danh và khung hình phạt.

## Phương pháp: bốn yếu tố cấu thành

Với mỗi yếu tố, ghi: quy tắc (trích điều) + chứng cứ (trích xuất) + kết luận
đạt/không đạt + độ tin cậy.

1. **Khách thể:** quan hệ xã hội được luật hình sự bảo vệ mà hành vi xâm hại.
2. **Mặt khách quan:** hành vi, hậu quả, quan hệ nhân quả, công cụ/phương tiện,
   thời gian/địa điểm — bám chứng cứ từng điểm.
3. **Chủ thể:** tuổi chịu trách nhiệm hình sự, năng lực trách nhiệm hình sự,
   chủ thể đặc biệt (nếu điều luật yêu cầu).
4. **Mặt chủ quan:** hình thức lỗi (cố ý trực tiếp/gián tiếp, vô ý), động cơ,
   mục đích — chỉ kết luận khi chứng cứ đủ, không suy đoán.

## Kết luận tội danh và khung

- Tội danh chính + điều/khoản + khung hình phạt (khoản áp dụng, mức phạt).
- Tội danh cạnh tranh: liệt kê và nêu yếu tố nào không đạt nên loại.
- Không ép tội: thiếu yếu tố cấu thành thì ghi rõ, đề xuất hướng thu thập
  thêm thay vì kết luận gượng.

## Output contract (cho QC reviewers)

`{"toi_danh":"...","dieu":"...","khung":"...","do_tin_cay":"cao|trung binh|thap","yeu_to_thieu":[...],"toi_danh_canh_tranh_loai":[...]}`
