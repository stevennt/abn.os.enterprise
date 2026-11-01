# The three planes, explained without the architecture

If you have ten minutes and you are new to this program, read this page. It
explains the same thing as the contract, in ordinary language, and it says what
you personally have to do. The formal version is
`docs/core/paperclip-integration.md`; you do not need it to understand this.

## In one minute

```
   design plane                 execution plane              tenant plane
+------------------+          +------------------+        +--------------------+
|  THE MODEL       | compile  |  PAPERCLIP       |  asks  |  OPENGATE          |
|  who works where |--------->|  tasks, agents,  |------->|  files, cases,     |
|  processes,rules |  (once)  |  runs, reviews   |  pass  |  people, log, bill |
+------------------+          +------------------+        +--------------------+
                                      |   works through         ^
                                      +-------------------------+
                                         tools, never raw data
```

A customer's company is described in **this repository**: who works there, which
departments exist, what a process looks like, which rules apply. That description
is the **design plane** — it is paper, not a running system.

The work itself happens in **Paperclip**: a task is written, an agent wakes up,
does the task, and the work is reviewed. That is the **execution plane**.

The customer's actual data — their files, their cases, their people, their bill —
lives in **OpenGate**. That is the **tenant plane**. It is also the only place
that can prove what happened, because it keeps the log.

So: the model says what the company is, Paperclip is where the agents work, and
OpenGate holds the customer's data and the evidence. No two of them own the same
thing.

## Follow one task

1. A manager writes a task in Paperclip: "check this loan file".
2. An agent is assigned. When it wakes, it does not get to guess who it is — it
   asks OpenGate for a pass: which customer, which company, which role, which
   folder it may open, whether the document is confidential.
3. The agent works only through OpenGate's tools. If it tries a folder it is not
   allowed to open, the tool refuses and records the refusal. The agent cannot
   argue its way past it, because the check is in the tool, not in the
   instructions.
4. What the agent produces is filed in OpenGate as the **record** — a case
   document, not a comment in a task.
5. OpenGate writes one line in the customer's log: who acted, on what, under
   which rule. If the work costs money, a second record goes to the bill.
6. The task in Paperclip closes with a link to the record. The customer sees the
   outcome and the cost line; the auditor sees the log.

## Who does what

- **The customer's admin** invites people, sets folders and permissions, and
  reads the bill. They never see the model repository.
- **The operator** compiles the customer's model into a team of agents, runs the
  go/no-go checks (the pre-live checklist: pack, plan, people, folders, SSO,
  scorecard), and is on call when something breaks. The rotation and page rules
  are set by the on-call workstream, not on this page.
- **An agent** has a role, a place in the org, and a named human responsible for
  it — the name is recorded on the agent, and it means that person answers for
  what the agent does and signs the sensitive steps. The agent has no password
  and no access outside the customer's pass.
- **An auditor** reads the log and the records. Nothing has to be reconstructed
  from chat.

## Five questions people ask

**Is Paperclip replacing OpenGate?** No. Paperclip runs the work; OpenGate holds
the customer's data and the proof. If Paperclip disappeared tomorrow, the
customer's files and history would still be there.

**Where does the org chart live?** In this repository, as part of the customer's
model. Paperclip gets a copy when we compile the team; it does not become the
source.

**Can an agent read another customer's files?** Not through any supported path.
The pass it receives names one customer, and every tool checks that name. A
refusal is recorded, including the rule that refused.

**What happens if Paperclip is down?** Agents stop; the customer's portal and
their records do not. Work stays in Paperclip's own queue, and when it comes back
the assigned agent resumes or a human reassigns the task. If OpenGate is the one
that is unreachable, the run does not start at all (no pass, no work) and the
task goes back to the queue with the reason.

**Who owns the cost number the customer sees?** OpenGate, from its own metering
(the records it keeps of what was used). Paperclip can stop an agent when a
budget is hit, but it does not produce the invoice.

**Who decides the folder rule?** The customer's admin owns it; the operator
records it when they ask; the platform enforces it in the tool. A refusal is
visible to the admin and the operator, and repeated refusals are treated as an
incident, not as noise.

## Words we use

| Word | What it means here |
|---|---|
| **tenant** | one customer, with one identity tree and one bill |
| **company** | a legal entity inside a tenant; a group has several |
| **unit / role** | a department and the job someone (or an agent) holds there |
| **model** | the description of a company: org, processes, rules |
| **pin** | the contract release a model was built from (`contract-YYYY.MM.N` + commit) |
| **compiled** | the model turned into a team of agents and routines |
| **template** | the compiled team that Paperclip imports |
| **pass** / **run context** | what an agent gets before it works: who it is, what it may touch |
| **activity event** | one line the platform records when work happens |
| **record** | what the customer keeps: a case document, a decision, a file |
| **metering** | the usage records behind the bill (runs, storage, documents) |
| **boundary version** | `paperclip-boundary@1.0` — the version of all of the above |

## Try it in ten minutes

1. Read this page, then skim the contract's three-plane diagram.
2. Run the two checks that keep this honest:
   `python scripts/check_plane_boundary.py` and
   `python scripts/test_plane_contract.py`.
3. Open the issue board (label `paperclip`) and read one **tier-1** issue in your
   area — tier 1 is the first 100 tasks, the ones that build the spine; the body
   says what "done" means and how to prove it.
4. If you need the log-retention answer for a customer, it is per tenant in the
   retention policy (`docs/retention.md` in the platform repo), not here.

## How we know this page is clear

A fresh reader — an agent with no context beyond this file — was asked the five
questions above and to name anything it could not act on. The result, and what
changed because of it, is in
`docs/core/paperclip-reviews/PC1-01-09-explainer.md`.
