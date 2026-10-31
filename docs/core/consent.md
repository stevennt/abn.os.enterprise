# Consent management v1.0 (issue #47) — VN PDPD (Decree 13) + bank secrecy

Every data use needs a receipt. No receipt, no processing — flows check consent
at the touchpoint before collecting or using PII (H77 templates carry the receipt id).

## Consent lifecycle states

```
GRANTED (purpose-scoped, timestamped, channel-recorded)
  -> WITHDRAWN (customer revokes; stops future use, keeps past lawful basis)
  -> EXPIRED (purpose fulfilled or term ended; same effect as withdrawn)
  -> RENEWED (fresh grant supersedes; old receipt archived, never edited)
```

Receipt = `{receipt_id, customer_id, purposes[], granted_at, channel, version}`.
Purposes are narrow (`onboarding-kyc`, `marketing-sms`, `credit-bureau-check`) —
blanket "I agree to everything" receipts are invalid and rejected at capture.

## Withdrawal flow

1. Customer withdraws (any channel: app, branch, call) → receipt flips WITHDRAWN in <5 min.
2. Propagation fan-out within 1h: marketing suppression, bureau-check block,
   AI-training exclusion, partner notification where contracts require.
3. In-flight instances finish (lawful basis at collection time stands) but spawn
   no new PII uses; new instances requiring that purpose divert to consent-capture.
4. Legal-hold exception: withdrawn data under STR/court hold is sealed, not deleted —
   MLRO attests the hold; deletion resumes after release (E48 retention).
5. Confirmation receipt sent to the customer (TP-C) with what stopped and what
   legally must be kept.
