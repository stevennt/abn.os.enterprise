# Branch/RM tablet journey v1.0 (issue #73) — assisted mode, same engine underneath

Branch is not a second system: the tablet drives the SAME flows/events/rules as
mobile; only the actor differs (staff-assisted, customer-present).

## Assisted-mode requirements

- Staff login (role queue, B17) + customer consent capture FIRST (E47 receipt on
  tablet) before any PII is entered or read aloud.
- Same screens as customer app plus: doc-scan assist, override lane (branch_manager,
  B11), e-sign on tablet (F57), print-on-demand for receipts.
- Dual control for cash/override actions (maker = RM, checker = branch_manager, B19).
- Session hygiene: auto-lock 2 min idle, one-tap handoff between tablets, full
  logout wipes cached PII; nothing persists on device (D33).
- Offline queue (H80): capture works without network, syncs with idempotency keys
  (A07) — conflicts resolve server-side, never by overwrite.
- Every assisted action is audit-logged with BOTH staff id and customer consent ref.
