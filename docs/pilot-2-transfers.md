# Pilot 2: transfers auto-routing v1.0 (issue #93) — highest volume, lowest risk slice

First L4 money in production: clean small transfers auto-post; everything else REVIEW.

## Threshold table (VND, NAPAS domestic)

| Band | Treatment |
|---|---|
| <50M, clean sanctions + limits | L4 auto-post (s1–s6 straight) |
| 50M–1B | L3 (operator release, B15) |
| >1B or sanctions gray | REVIEW + manager (hold lane) |
| any duplicate key | cached response, zero re-post (A07) |
| after cut-off 16:00 | next-day value-date, same bands |

Bands tighten automatically on DQ/lag breach (D38/H75) and loosen only via rule PR (E46).

## Reconciliation check (continuous, not end-of-day)

- Per-1000-transfer micro-recon: core postings vs engine outcomes vs notification log —
  mismatch halts auto-posting to REVIEW in <60s.
- End-of-day full recon to the cent; any break = Sev1 + L4 suspension until root-caused.
- Customer-visible proof: txn ref traceable in app to audit verify (E49).
