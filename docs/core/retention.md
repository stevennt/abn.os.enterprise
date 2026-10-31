# Retention & e-archiving policy v1.0 (issue #48)

## Retention table per doc type

| Doc type | Keep | Where | Retrieval SLA |
|---|---|---|---|
| money-movement records (txns, postings, batches) | 7y (2555d) | core + topics + cold archive | 4h hot, 2d cold |
| loan/credit files (apps, decisions, collateral) | 7y after closure | LOS + sealed store | 4h hot, 2d cold |
| KYC packs + UBO | 7y after relationship end | sealed store | 1d (gated) |
| STR packs + filings | 7y after filing | sealed store (MLRO-gated) | 1d (MLRO only) |
| complaints + outcomes | 3y | CRM + warehouse | 4h |
| HR records | 3y (recruit rejects: 1y) | HRMS | 1d |
| audit chain + DLQ | 7y chain / 90d DLQ hot | audit topic + sealed store | 1h |
| consent receipts | life of relationship + 3y | consent store | 1h |
| notifications/logs (non-PII) | 1y | log store | 4h |
| sandbox/synthetic data | 90d | stage only, auto-purge | n/a |

## E-archiving rules

- Write-once format (PDF/A for human docs, canonical JSON for machine records) with
  sha256 manifest per archive batch; manifest hashes chained monthly.
- Legal holds suspend deletion per matter (MLRO/court attested); holds reviewed quarterly.
- Purge jobs run monthly with dry-run report first; any purge touching sealed data
  needs dual approval. Deletion is cryptographic erasure of the data key + tombstone.
