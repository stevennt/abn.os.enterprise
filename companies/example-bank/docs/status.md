# example-bank — status

- **Shape:** scaffold. Departments, units and flow references exist so the model
  validates; the content (mandates, headcount, RACI, systems) is not real.
- **Contract pin:** `contract-2026.11.1` at
  `a7baab409dce013bd296b57aafc500565b878dfa`.
- **Industry:** `banking`, pack `banking-pack-2026.10.1`.
- **Mapping:** tenant `abnasia` (company #1) points at this model in
  `docs/core/company-mapping.md`; the pin above is the tenant pin.
- **Next:** replace the departments with the customer's, adopt the flows the
  company actually runs, and record the real headcount plan per unit.
