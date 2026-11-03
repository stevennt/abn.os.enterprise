# Secrets: references, not values — `secret-ref@1` (issue #412)

**Status:** specified (#412); the implementation (#413), its wiring (#414), the
matrix (#415), the record (#416), the console (#417), the runbook (#418),
hardening (#419), measures (#420) and the demo (#421) follow.

**Contract:** `schemas/secret-ref.json`. **Oracle:**
`scripts/check_secret_ref_spec.py` — it validates the shape and proves every refusal
below with `--self-test`. **Fixture:** `tests/fixtures/secrets/env.valid.json`.

Decision **D7** ([paperclip-integration.md](paperclip-integration.md)): secrets live
in the vault and Paperclip holds **references**. This contract is the interface that
makes D7 checkable instead of aspirational.

## The rule, in one sentence

**A run's environment carries a reference; the value exists only in the process that
uses it, for as long as it uses it.**

That is why the manifest can be kept: a reference survives in a record, a value
cannot. One rotation path (the vault), one injection point (the run env), and no
second copy anywhere — not in the template, the ticket, the prompt, the audit line or
the Paperclip database.

## Inputs

| Input | Where | What |
|---|---|---|
| the run env manifest | `customers/<tenant>/runs/<runId>.env.json` | the names the run gets, and a `vault://` reference for each |
| the process environment | the adapter's own environment | the values, injected at deploy from the vault |
| the run's required names | the manifest's `required[]` | what the run's tools cannot start without |

```json
{
  "version": 1,
  "contract": "secret-ref@1",
  "runId": "PC-1234-1",
  "tenant": "hvcs",
  "env": {
    "KIMI_API_KEY": "vault://os/prod.enc.yaml#providers.kimi.key",
    "SMTP_PASSWORD": "vault://os/prod.enc.yaml#mail.smtp.password"
  },
  "required": ["KIMI_API_KEY"]
}
```

**The reference is `vault://<file>#<key>`.** `<file>` is a path inside the vault
repository (`vault/os/prod.enc.yaml`), `<key>` a dot path inside the decrypted
document (`providers.kimi.key`). No scheme other than `vault`, no absolute paths, no
`..`, no query string — and the key is required, because a reference to a whole file
is not a reference to a secret.

**The manifest is evidence, so it stays.** It is written before the run and it is
never rewritten: it says which secret the run was told to use, and nothing about what
that secret was.

## The resolution

At run start, and only there:

1. the manifest is read and validated (shape, references, names, `required`);
2. each name is read from the **adapter's process environment** — the deploy put it
   there from the vault;
3. an absent or empty value **stops the run**; a run does not start with a secret it
   cannot read;
4. the resolved set is passed to the **child process** and to nothing else;
5. one line per name is appended to `customers/<tenant>/runs/<runId>.env.jsonl`:
   `{version, at, runId, name, ref, ok, code?}` — a name, a reference and an outcome.

```json
{"version": 1, "at": "2026-11-03T09:00:00Z", "runId": "PC-1234-1",
 "name": "KIMI_API_KEY", "ref": "vault://os/prod.enc.yaml#providers.kimi.key",
 "ok": true}
```

**Rotation does not touch a reference.** The value rotates in the vault and the
deploy; the manifest, the resolution lines, the audit and every other record stay
byte-identical. That is the whole return on D7: one path to rotate, no consumers to
update.

## What never happens

- a value in the manifest, the resolution lines, the audit line, metering or the
  template — and never in a prompt;
- a value, a prefix of one, or a hash of one in a record: a reference is the only
  thing a record may carry (`E-SEC-08` is the writer that refuses the rest);
- a secret inherited from the adapter's environment by the child without being
  declared: the child gets the **resolved declared set**, not a copy of the parent;
- a "temporary" copy for a retry: a retry re-reads the environment.

## Errors

| Code | What cannot proceed | Fix |
|---|---|---|
| `E-SEC-01` | the manifest carries a **value** where a reference belongs | move the value to the vault and put its reference in the manifest |
| `E-SEC-02` | the reference is malformed: another scheme, an absolute path, `..`, or no `#key` | write `vault://<file>#<key>` |
| `E-SEC-03` | the name is not in the adapter's environment — the deploy did not inject it | inject it from the vault at deploy; the run does not start without it |
| `E-SEC-04` | the variable exists but is empty or whitespace | fix the vault value; an empty secret is a missing secret |
| `E-SEC-05` | a name is not a POSIX environment name (`[A-Z_][A-Z0-9_]*`) | rename it; a name the shell cannot pass is not a name |
| `E-SEC-06` | a name the run declares as `required` is not in `env` | declare it, or stop requiring it |
| `E-SEC-07` | the manifest is missing or unreadable | fix the manifest; a run with no env manifest does not start |
| `E-SEC-08` | a resolution line tried to carry a value, or any part of one | record the name, the reference and the outcome — never the value |

Every refusal carries its fix in the message (`E-SEC-NN: … — fix: …`), and the
coverage rule is the same as the rest of this repository: **a broken input is
refused, never ignored.**

## What the oracle proves

`python scripts/check_secret_ref_spec.py` validates the fixture against the schema
and recomputes the rules a schema cannot express: every `env` value is a `vault://`
reference, every name is POSIX, `required` is a subset of `env`. Its `--self-test`
takes the **valid** fixture and breaks it eight ways — one per code — and fails if any
code does not appear with its fix. That is what CI runs, so the contract cannot drift
into prose.

## The seam this sits on

- **Enterprise OS** decides the policy (this document): what a run is given, and what
  a record may say about it.
- **Paperclip** holds the reference in the run's env manifest and nothing else (D7).
- **OpenGate** implements the resolution and the refusals (#413), records it (#416)
  and validates it in `--sync` (#416); the run context it already mints is the
  neighbouring seam ([paperclip-integration.md](paperclip-integration.md), seam 2).
- **The vault** (`abn.secrets.encrypted`) is the only place a value exists at rest.
