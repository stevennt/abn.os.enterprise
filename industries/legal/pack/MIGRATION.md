# Legal pack — migration notes

## [1.0.0] — imported from OpenGate (loop 4, issue #132), DRAFT

Structure moved; substance did not. What changed:

- `domains/legal/{agents,skills,roles.yaml,rules.md}` → `industries/legal/pack/`.
- `Product source: domains/legal/...` lines rewritten to `industries/legal/pack/...`.
- `rules.md` rewritten: it now cites `rules/legal-citation-pack.yaml` and
  `rules/legal-signoff-pack.yaml` by same-repo path, and carries an explicit
  `placeholder:` statement instead of naming instruments.
- Skill versions bumped to 1.1.0 where the body changed (path rewrites).

### Migration

No migration needed for agent behaviour: roles, rubrics, temperatures and step caps
are unchanged.

### Not moved on purpose

`scenarios/` (27 substantive scenario files), `corpus.md`, `retrieval.md`,
`connectors/` stay in the acquiring product. Reasons and the gate for adding them
are listed in `industries/legal/docs/placeholders.md`.

### Status

`pack.status: draft` — may be resolved for evaluation, must not be used for client
work until every placeholder row is closed by a named reviewer.
