# Stage env (issue #101) — Camunda 8.5.7 on Docker, trimmed official compose

## Run

```
cd engine/stage
docker compose up -d            # elasticsearch + zeebe + operate (auth: none, spike only)
./bin/zbctl deploy loan-flow.bpmn --insecure
ABNVENV/bin/python worker.py all   # completes bank-s1..s6
./bin/zbctl create instance loan.retail.unsecured --insecure --variables '{...}'
Operate UI: http://localhost:8081 (demo/demo, form login)
```

Files: `docker-compose.yml` (+`.env`, trimmed from upstream 8.5.0 CORE),
`loan-flow.bpmn` (mirrors `examples/bank/loan-approval.flow.yaml` + PT1M boundary
on s5), `worker.py` (pyzeebe job worker, modes all/no-s5/slow-s3), `bin/zbctl`.

## Evidence (2026-10-31, all on this stage)

- Instance A happy path: key 2251799813685265 — s1..s6 completed, PROCESS ELEMENT_COMPLETED.
- Instance B timer: key 2251799813685417 — s5 TERMINATED, s5-timer COMPLETED, f5t taken,
  escalated-end COMPLETED, s6 never activated.
- Instance C kill recovery: key 2251799813685520 — worker SIGKILLed mid-s3 (90s sleep),
  restarted worker reactivated s3 after lock timeout, s3..s6 completed, PROCESS COMPLETED.
- Gotchas recorded: boundary events need explicit `<bpmn:outgoing>`; pyzeebe handlers
  take no args; Operate core login is form-encoded (JSON 401s); Operate v1 REST needs
  session + forbids headless use here — verification done via Zeebe ES records (the same
  index Operate reads).
