# Automation levels L0–L5

| Level | Name | Who decides | Example (bank) |
|-------|------|-------------|----------------|
| L0 | Manual | human, no system | branch officer papers |
| L1 | Assist | human, AI drafts | AI pre-fills KYC form |
| L2 | Partial workflow | system routes, human executes | ticket assigned, officer clicks |
| L3 | Conditional auto + approve | system executes, human approves | loan scored auto, manager approves >500M VND |
| L4 | Full auto + override | system executes, human can override in T+X | eKYC auto-pass, officer reviews flags only |
| L5 | Autonomous + self-improve | system executes + tunes thresholds, human audits | fraud thresholds auto-tuned weekly, audit monthly |

**Promotion gate L3→L4:** eval set green + 30d error rate < threshold + rollback plan + rule-version pinned.
**Demotion rule:** any Sev1/regulatory breach auto-demotes to L3 and opens an incident issue.
