# income-verify + fraud-signal spec v1.0 (issue #63)

## Feature list (no raw PII — hashed ids, bucketed amounts)

Consistency: declared-vs-payslip ratio, declared-vs-statement-inflow ratio,
employer-name match (fuzzy), tenure bucket, income-roundness flag.
Fraud signals: multi-application velocity (7d/30d), device/id reuse across
customers, employer blacklists hits, document-tamper score from s2, first-seen
account patterns. All features versioned with the model card (D35 discipline).

## Calibration plot requirement

Scores must be calibrated probabilities, not ranks: quarterly reliability plot
(predicted vs observed default/fraud rate per decile) on the trailing window,
max deviation 5pp per decile or the model is pulled to REVIEW-only until refit.
The plot + table ship inside every eval report (G67) and the promotion gate (A10)
reads them. Uncalibrated-but-accurate is still a fail — thresholds assume calibration.

## Targets

- Calibration deviation ≤5pp per decile, quarterly window.
- Consistency-check precision ≥0.95 on golden pairs; fraud recall ≥0.90 at review rates the business signs off.
