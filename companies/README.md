# Companies — per-company operating models

One folder per company, built from this repo's contract: a company is a legal
entity inside an OpenGate tenant (`tenant` + `entity`), it runs on one
industry's flows/rules/packs, and it **pins the contract release** it was built
from (`contract.tag` + `contract.sha`).

```
companies/<id>/
  company.yaml          the model (schema: companies/company.schema.yaml)
  org/org-chart.yaml    units + parent + headcount (industries' org shape)
  docs/status.md        what is real and what is still a scaffold
```

Scaffold one with `bin/new-company` (see `docs/core/onboarding-company.md`), then
run `python scripts/validate_company.py`. CI runs the same check and the
self-test, so a broken model cannot land.

Why a folder and not always a repo: the model is small and shares the contract's
validation; when a customer's model needs its own lifecycle (or its tier moves
to `restricted`), copy the folder into a repo and vendor the contract at the
pinned tag — `docs/core/onboarding-company.md` has the recipe. The pin is what
makes the split safe: the copy is reproducible from the tag+sha.
