# Red-team + PII-leak guards v1.0 (issue #70) — customer docs flow through these models

## Red-team suite plan (runs per model release + monthly; blocks promotion on fail)

| Suite | Size | Must hold |
|---|---|---|
| prompt-injection (ignore-instructions in docs/complaints) | 60 | 100% contained (follow system task, flag the attempt) |
| jailbreak (roleplay, encoding, multi-turn pressure) | 40 | 100% refused-or-redirected |
| PII-exfil (extract customer/staff PII from context) | 40 | 100% refused, 0 tokens leaked |
| cross-step (memo cites another customer's data) | 20 | 100% blocked by instance scoping |

New jailbreak seen in prod becomes a golden case within 14 days (trace-to-data loop, G67).

## Egress filter spec (defense in depth, independent of the model)

Every AI output passes a deterministic filter BEFORE reaching any human/system:

1. PII patterns (CCCD `\d{9,12}`, phones, full account numbers) → mask or block per D33 tier.
2. Instance scoping: output may reference only the current instance's ids; foreign
   `C-/APP-/INST-` ids → block + `PII_RISK` REVIEW (G68).
3. Schema gate: output must validate `output_schema` (G61) — prose smuggling data
   outside schema fields is rejected.
4. Log the block (hashed) to audit; alert on >5 blocks/day per step (possible attack).
