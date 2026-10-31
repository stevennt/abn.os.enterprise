# Event catalog v1.0 (issue #31) — every trigger named, versioned, owned

## Naming convention

- Shape: `<domain>.<entity>.<past-tense-verb>` — all lowercase, dots only.
  Good: `loan.application.submitted`. Bad: `LoanApplicationCreated`, `loan_app_submitted`.
- Verb is past tense (the thing already happened): `requested`, `opened`, `received`,
  `approved`, `filed`, `decided`, `started`, `declared`, `hit`, `due`.
- Version = payload-contract semver (A06). Consumers pin major.minor (A04).
- Owner = the unit that owns the producer; producer must exist before the event ships.

## Catalog (40 trigger events)

| event | ver | owner | process |
|---|---|---|---|
| `ekyc.onboarding.requested` | 1.0.0 | retail | ekyc.onboarding |
| `loan.application.submitted` | 1.0.0 | retail.credit | loan.retail.unsecured |
| `loan.mortgage.requested` | 1.0.0 | retail.credit | loan.retail.mortgage |
| `deposit.open.requested` | 1.0.0 | retail | deposit.open |
| `card.issue.requested` | 1.0.0 | retail | card.issue |
| `card.dispute.opened` | 1.0.0 | cards | card.dispute |
| `loan.corporate.term.requested` | 1.0.0 | corporate | loan.corporate.term |
| `loan.corporate.wc.requested` | 1.0.0 | corporate | loan.corporate.working_capital |
| `account.corporate.open.requested` | 1.0.0 | corporate | account.corporate.open |
| `guarantee.issue.requested` | 1.0.0 | corporate | guarantee.issue |
| `risk.scoring.requested` | 1.0.0 | risk | risk.scoring.retail |
| `risk.limit.review.due` | 1.0.0 | risk | risk.limit.review |
| `risk.early_warning.fired` | 1.0.0 | risk | risk.early_warning |
| `aml.screening.hit` | 1.0.0 | compliance | aml.str.filing |
| `kyc.refresh.due` | 1.0.0 | compliance | kyc.refresh |
| `sanction.check.requested` | 1.0.0 | compliance | sanction.check |
| `fx.quote.requested` | 1.0.0 | treasury | fx.quote |
| `mm.borrowing.instructed` | 1.0.0 | treasury | mm.borrowing |
| `liquidity.report.due` | 1.0.0 | treasury | liquidity.report |
| `transfer.domestic.requested` | 2.0.0 | payments | transfer.domestic |
| `transfer.swift.requested` | 1.0.0 | payments | transfer.swift |
| `salary.batch.uploaded` | 1.0.0 | payments | salary.batch |
| `billpay.topup.requested` | 1.0.0 | payments | billpay.topup |
| `auth.fraud.hold.decided` | 1.0.0 | cards | auth.fraud.hold |
| `card.reissue.requested` | 1.0.0 | cards | card.reissue |
| `installment.convert.requested` | 1.0.0 | cards | installment.convert |
| `lc.issue.requested` | 1.0.0 | trade | lc.issue |
| `lg.claim.received` | 1.0.0 | trade | lg.claim |
| `doc.collection.received` | 1.0.0 | trade | doc.collection |
| `complaint.received` | 1.0.0 | cs | complaint.handle |
| `call.verify.requested` | 1.0.0 | cs | call.verify |
| `branch.appointment.booked` | 1.0.0 | cs | branch.appointment |
| `hr.recruit.decided` | 1.0.0 | hr | hr.recruit.offer |
| `hr.offer.accepted` | 1.0.0 | hr | hr.onboard.employee |
| `hr.leave.requested` | 1.0.0 | hr | hr.leave.approve |
| `hr.exit.initiated` | 1.0.0 | hr | hr.offboard.exit |
| `ap.invoice.received` | 1.0.0 | finance | finance.ap.invoice |
| `gl.close.month.started` | 1.0.0 | finance | finance.gl.close.month |
| `incident.p1.declared` | 1.0.0 | itops | incident.p1 |
| `batch.eod.started` | 1.0.0 | itops | batch.eod |
