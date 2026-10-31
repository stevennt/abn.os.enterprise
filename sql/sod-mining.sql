-- SoD mining queries v1.0 (issue #117, spec I88) — run quarterly on the audit export.
-- Table: audit_actions(instance_id, actor, actor_role, action, target_role, decided_at)
-- action in (MAKER_SUBMIT, CHECKER_APPROVE, DELEGATE_GRANT, FILING_SUBMIT, OVERRIDE_GRANT).

-- Q1: maker == checker on one instance (universal ban).
SELECT instance_id, actor FROM audit_actions
WHERE action IN ('MAKER_SUBMIT','CHECKER_APPROVE')
GROUP BY instance_id, actor HAVING COUNT(DISTINCT action) = 2;

-- Q2: investigator filed own STR case.
SELECT instance_id, actor FROM audit_actions
WHERE action IN ('MAKER_SUBMIT','FILING_SUBMIT')
GROUP BY instance_id, actor HAVING COUNT(DISTINCT action) = 2;

-- Q3: delegate acted as checker where delegator was maker.
SELECT d.instance_id, d.actor FROM audit_actions d
JOIN audit_actions m ON m.instance_id = d.instance_id
  AND m.action = 'MAKER_SUBMIT' AND d.action = 'CHECKER_APPROVE'
JOIN audit_actions g ON g.action = 'DELEGATE_GRANT'
  AND g.actor = m.actor AND g.target_role = d.actor_role;

-- Q4: approvals above personal band (band passed as :band_csv per role in app layer;
-- here: any CHECKER_APPROVE flagged over_band=1 by the exporter).
SELECT instance_id, actor FROM audit_actions
WHERE action = 'CHECKER_APPROVE' AND over_band = 1;

-- Q5: MLRO-delegated filing (non-delegable power exercised by another).
SELECT instance_id, actor FROM audit_actions
WHERE action = 'FILING_SUBMIT' AND actor_role != 'mlro';

-- Q6: emergency delegations >48h or without next-day review.
SELECT instance_id, actor FROM audit_actions
WHERE action = 'DELEGATE_GRANT' AND (hours_valid > 48 OR reviewed_next_day = 0);
