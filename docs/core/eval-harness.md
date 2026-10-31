# Eval harness v1.0 (issue #67) — one runner, promotion gates read its report

Run: `python scripts/eval_harness.py [--strict]`. Exit 0 = all suites green.

## Design

- Discovery: every `ai/*.contract.yaml` must point at an existing `eval_suite` dir
  containing `README.md` with a Targets section (metrics + thresholds).
- Executable checks: any `test_*.py` inside a suite dir runs; failures fail the harness.
- Model-bump regression: same suites re-run at the new pinned version; report diffs
  fail the release unless risk signs the delta (A10 reads this report).
- `--strict` additionally requires ≥100 golden docs per suite README claim (counts
  `golden/` files when materialized, track-G build).

## Suite inventory

| Suite (contract) | Golden size | Gate metrics |
|---|---|---|
| evals/doc-extract (s2-extract) | 300 docs | F1≥0.97 clean, numbers exact-match≥0.99, abstain@0.70 |
| evals/income-verify (s3-income-verify) | rolling window | calibration ≤5pp/decile quarterly |
| evals/memo-draft (s5-memo-draft) | 200 memos + 30 adv | grounding 100%, citation 100% |
| evals/complaint-triage (s1-triage) | 200 complaints | S1/S2 recall 1.00, intent≥0.90, tone+policy |
| evals/policy-copilot (copilot-qa) | 150 Q&A + 30 OOC + 20 probes | grounded≥0.95, OOC abstain 100%, PII refuse 100% |

## Failure-mode intake loop

New failure modes found in prod (missed fraud, bad abstain, leaked PII, wrong cite)
become golden rows within 14 days: reproduce minimal synthetic case → append to the
suite's `golden.jsonl` via `gen_goldens.py` input seeds → re-freeze manifest → harness
must catch the original failure (regression proof) before the fix ships. No fix lands
without its golden.
