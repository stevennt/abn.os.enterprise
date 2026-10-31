# File/docs service v1.0 (issue #57) — upload to e-sign, nothing raw in the open

Every loan/complaint carries documents (CCCD, income, contracts). Files live in the
sealed store (D33/E48); flows and audit hold only `doc_ref` + sha256, never bytes.

## Lifecycle (+ retention link)

```
upload (signed URL, 15-min expiry) -> virus-scan (quarantine on hit)
  -> store sealed (AES-256, per-file data key) -> link to instance (doc_ref)
  -> e-sign (OTP-backed, signer identity bound) -> retain per E48 -> purge
```

Retention links: KYC docs 7y post-relationship, credit docs 7y post-closure,
complaint attachments 3y (E48 table). Purge = crypto-shred the data key + tombstone.

## Virus-scan + size policy

- Scan BEFORE store: ClamAV + sandbox detonation for office/PDF macros; unscannable
  (encrypted/unknown) files are rejected, never stored pending.
- Size: 10MB/file, 50MB/instance; images auto-downscaled server-side after scan.
- Types allowlist: pdf/jpg/png (+ office for corporate); executables never accepted.
- E-sign: Vietnamese e-contract compliant (OTP + timestamp + signer CCCD binding);
  signed PDF/A archived write-once with the instance audit tail attached.
