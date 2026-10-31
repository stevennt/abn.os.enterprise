#!/usr/bin/env python3
"""Stage job worker (issue #101): completes bank-s* jobs for the loan flow.
Modes (argv): all | no-s5 (timer demo: never touch s5) | slow-s3 (kill demo: sleep in s3)
Logs every activation/completion to worker.log (evidence for recovery demo).
"""
import asyncio, sys, time
from pyzeebe import ZeebeWorker, create_insecure_channel

LOG = "/Users/thanhson/Workspace/abn.os.enterprise/engine/stage/worker.log"
MODE = sys.argv[1] if len(sys.argv) > 1 else "all"

def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    open(LOG, "a").write(line + "\n")

async def main():
    worker = ZeebeWorker(create_insecure_channel("127.0.0.1:26500"))

    @worker.task(task_type="bank-s1", timeout_ms=15000)
    async def s1(): log("s1-verify done"); return {"outcome": "PASS"}

    @worker.task(task_type="bank-s2", timeout_ms=15000)
    async def s2(): log("s2-extract done"); return {"outcome": "FIELDS"}

    @worker.task(task_type="bank-s3", timeout_ms=20000)
    async def s3():
        if MODE == "slow-s3":
            log("s3-score START slow (90s) — kill me now for recovery demo")
            await asyncio.sleep(90)
        log("s3-score done"); return {"outcome": "PASS"}

    @worker.task(task_type="bank-s4", timeout_ms=15000)
    async def s4(): log("s4-aml done"); return {"outcome": "CLEAR"}

    if MODE != "no-s5":
        @worker.task(task_type="bank-s5", timeout_ms=15000)
        async def s5(): log("s5-decide done"); return {"outcome": "APPROVE"}

    @worker.task(task_type="bank-s6", timeout_ms=15000)
    async def s6(): log("s6-notify done"); return {"outcome": "SENT"}

    log(f"worker up mode={MODE}")
    await worker.work()

asyncio.run(main())
