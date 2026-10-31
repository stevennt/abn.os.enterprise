# Touchpoint taxonomy C/E/S/X

- **C customer:** mobile app, SMS, Zalo OA, branch counter, ATM, callbot. Needs consent + VI templates + 5-min SLA on status pushes.
- **E employee:** inbox (Frappe), email, RM tablet. Needs delegation, SLA escalation, SoD.
- **S system:** core banking, CIC, NAPAS, SWIFT, e-sign, eKYC provider. Needs adapter + timeout + retry + circuit-breaker.
- **X external:** SBV reporting, auditor, insurer, partner. Needs signed payloads + retention.

Every touchpoint file lists: party, channel, SLA, template, 2-way?, fallback channel.
