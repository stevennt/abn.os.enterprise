# Fresh-reader check — the three planes explainer (PC1-01-09, issue #250)

- **Page tested:** `docs/core/paperclip-explainer.md`
- **Reader:** a fresh agent with no context. Instruction: read **only** that file,
  answer five questions, then name anything it could not act on, any undefined
  term, and anything it expected but did not find. No repo search, no other file.
- **Date:** 2026-11-01.

## What it got right (no fix needed)

| Question | Reader's answer | Verdict |
|---|---|---|
| Three planes, which holds customer data? | design = this repo (paper); execution = Paperclip; tenant = OpenGate, and it holds the log | correct |
| Who decides folder access? | the tool, not the instructions; the pass names the customer, and a refusal is recorded | correct on enforcement, silent on who *sets* the rule |
| Where does work become the durable record? | OpenGate, as a case document; the task closes with a link | correct |
| Paperclip down? | agents stop, portal and records do not | correct but incomplete (where the queue lives) |
| Who owns the cost number? | OpenGate metering; Paperclip only throttles | correct |

## What it flagged, and what changed

| Flag | Fix in the page |
|---|---|
| "Nothing is lost — tasks stay queued" — queued where, how long? | now: "stays in Paperclip's own queue; when it comes back the assigned agent resumes or a human reassigns"; and the reverse case: OpenGate unreachable → no pass, no run, task returns to the queue with the reason |
| "a named human responsible for it" — named where, obliges what? | now: "the name is recorded on the agent, and it means that person answers for what the agent does and signs the sensitive steps" |
| operator "on call" has no SLA or escalation | now: the rotation and page rules are set by the on-call workstream, and the page says so instead of implying an SLA |
| "who decides the folder rule?" not answered | new question: the admin owns it, the operator records it, the platform enforces it; a refusal is visible and repeated refusals are an incident |
| undefined: *pins, pass, metering, readiness/go/no-go, tier-1 issue, compiled* | all six now defined in the glossary or in place |
| expected a diagram; the page only pointed at the contract | a three-plane ASCII diagram with the compile arrow, the pass, and the tool path is now at the top |
| expected: agent mid-task when OpenGate is unreachable; log retention; refusal escalation | the first and third are now answered; retention is delegated with a pointer (per-tenant policy in the platform repo) |

## Verdict

**Pass after one revision.** The five questions were all answered from the page
alone; the fixes are vocabulary and the three operational holes the reader found
(queue location, responsibility semantics, refusal escalation). No sentence now
requires the contract to be understood.

## How to repeat this

Run the same prompt against the page after any change to it or to the contract
(clause: the explainer is checked whenever the boundary version bumps). The check
is cheap and catches the failure the contract tests cannot: a page that is
internally consistent and still does not teach.
