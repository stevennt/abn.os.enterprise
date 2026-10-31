# Idempotency + exactly-once guidance v1.0 (issue #7)

Money must never move twice because a message arrived twice. Rule of thumb:
**derive the key before any side effect, check-then-act atomically, cache the
response by key.** At-least-once delivery + idempotent handlers = effectively-once.

## Key-derivation table (all 46 catalog flows; "40" in planning ≈ this set)

Format: `trigger event → idempotency key formula (scope, TTL)`.

| # | Trigger event | Key formula | Scope / TTL |
|---|---|---|---|
| 1 | ekyc.onboarding.requested | `cccd_hash + channel` | customer / 90d |
| 2 | loan.retail.unsecured.requested | `customer_id + application_id` | application / 7y |
| 3 | loan.retail.mortgage.requested | `customer_id + application_id` | application / 7y |
| 4 | deposit.open.requested | `customer_id + product + request_id` | request / 7y |
| 5 | card.issue.requested | `customer_id + card_product + request_id` | request / 7y |
| 6 | card.dispute.opened | `card_id + txn_id + reason_code` | dispute / 7y |
| 7 | loan.corporate.term.requested | `tax_id + facility_id` | facility / 7y |
| 8 | loan.corporate.wc.requested | `tax_id + facility_id + tranche_no` | tranche / 7y |
| 9 | account.corporate.open.requested | `tax_id + request_id` | request / 7y |
| 10 | guarantee.issue.requested | `tax_id + guarantee_ref` | instrument / 7y |
| 11 | risk.scoring.requested | `customer_id + scoring_date + model_ver` | day / 90d |
| 12 | risk.limit.review.due | `entity_id + period` | period / 1y |
| 13 | risk.early_warning.fired | `entity_id + signal + date` | day / 1y |
| 14 | aml.screening.requested | `entity_id + payload_hash` | payload / 1y |
| 15 | aml.str.case.opened | `case_id` | case / 7y |
| 16 | kyc.refresh.due | `customer_id + cycle` | cycle / 1y |
| 17 | sanction.check.requested | `entity_id + list_version + payload_hash` | check / 1y |
| 18 | fx.quote.requested | `client_id + ccy_pair + quote_id` | quote / 30d |
| 19 | mm.borrowing.instructed | `deal_ref` | deal / 7y |
| 20 | liquidity.report.due | `date + entity` | day / 1y |
| 21 | transfer.domestic.requested | `client_key(header) ?? sender + payee + amount + rail + minute` | money / 7y |
| 22 | transfer.swift.requested | `client_key(header) ?? sender + uetr` | money / 7y |
| 23 | salary.batch.uploaded | `batch_id + line_no` | line / 7y |
| 24 | billpay.topup.requested | `client_key(header) ?? payer + biller + amount + minute` | money / 7y |
| 25 | auth.fraud.hold.decided | `card_id + auth_code` | auth / 90d |
| 26 | card.reissue.requested | `card_id + reason + request_id` | request / 90d |
| 27 | installment.convert.requested | `card_id + txn_id` | txn / 7y |
| 28 | lc.issue.requested | `applicant_tax + lc_ref` | instrument / 7y |
| 29 | lg.claim.received | `lg_ref + claim_id` | claim / 7y |
| 30 | doc.collection.received | `collection_ref + doc_hash` | doc / 7y |
| 31 | complaint.received | `channel + external_ticket_id` | ticket / 3y |
| 32 | call.verify.requested | `customer_id + call_id` | call / 90d |
| 33 | branch.appointment.booked | `customer_id + slot_id` | slot / 90d |
| 34 | recruit.offer.approved | `candidate_id + req_id` | req / 1y |
| 35 | onboard.employee.started | `employee_id + start_date` | employee / 3y |
| 36 | leave.approve.requested | `employee_id + leave_id` | leave / 1y |
| 37 | perf.review.submitted | `employee_id + cycle` | cycle / 3y |
| 38 | offboard.exit.initiated | `employee_id + exit_id` | exit / 3y |
| 39 | ap.invoice.received | `vendor_tax + invoice_no` | invoice / 7y |
| 40 | gl.close.month.started | `period + entity` | period / 7y |
| 41 | tax.vat.file.due | `period + entity + form` | filing / 7y |
| 42 | budget.request.submitted | `dept + period + request_id` | request / 3y |
| 43 | incident.p1.declared | `monitor + alert_id` | alert / 1y |
| 44 | change.deploy.approved | `service + change_id` | change / 1y |
| 45 | access.grant.requested | `user + resource + request_id` | grant / 1y |
| 46 | batch.eod.started | `date + system` | day / 1y |

Money-movement keys live ≥7y (match E48 retention). `client_key` = caller-supplied
`Idempotency-Key` header; the `??` fallback is hashed server-side and returned so
the caller can reuse it. Never put wall-clock time or randomness in a key.

## Retry-safe checklist (every handler, reviewed at PR)

- [ ] Key derived FIRST, before any DB write, API call, or message send.
- [ ] Atomic `insert-if-absent` into processed-keys store; duplicate → return cached response, do zero work.
- [ ] Response cached by key (same bytes on replay, including generated ids/refs).
- [ ] Each downstream side effect carries the key (core txn ref, GL narration, SMS batch id).
- [ ] Handlers are pure re-runnable: no `now()` in business logic (inject clock), no random without seed.
- [ ] Consumer commits offset only AFTER handler success + response cache write.
- [ ] DLQ on poison (not infinite retry): 5 attempts, exponential backoff, then DLQ per A04.

## Duplicate-injection test plan

- **Unit:** harness replays every trigger 3× (immediate, +5min, cross-partition) into a
  sandbox; assert exactly one business effect + byte-identical responses.
- **Kill-mid-handler:** SIGKILL the worker between side effect and offset commit;
  redeliver; assert no double-post (nightly in stage).
- **Money drill (monthly):** 10k synthetic transfers, 15% duplicates, multi-day clock
  skew; assert ledger balance + zero double-posts.
- **Gate:** green injection suite is required for any L3→L4 promotion (I83 reads it).
