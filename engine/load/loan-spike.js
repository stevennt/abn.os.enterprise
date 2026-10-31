import { check } from 'k6';
import http from 'k6/http';
import { SharedArray } from 'k6/data';

// L2-104: loan spike against stage (or local stub). Mix 80/15/5 clean/review/duplicate.
const BASE = __ENV.BASE_URL || 'http://127.0.0.1:8099';
const SMOKE = __ENV.SMOKE === '1';
export const options = {
  stages: SMOKE
    ? [{ duration: '20s', target: 5 }]
    : [
        { duration: '5m', target: 17 },   // ramp to 1000 apps/hour
        { duration: '30m', target: 17 },  // hold
        { duration: '5m', target: 34 },   // 2x spike
        { duration: '2m', target: 0 },    // down
      ],
  thresholds: {
    http_req_failed: ['rate<0.01'],       // SLO: errors <0.1% (F60, 10x margin in smoke)
    http_req_duration: ['p(95)<2000'],    // stub-local proxy; stage asserts TTA separately
  },
};
let n = 0;
export default function () {
  n += 1;
  const kind = n % 20;
  const dup = kind >= 18 && kind < 20;                    // 5% duplicates
  const review = kind >= 15 && kind < 18 && !dup;         // 15% review
  const key = dup ? 'IDEM-SMOKE-DUP' : `IDEM-${__VU}-${n}`;
  const payload = JSON.stringify({
    customer_id: 'C-TEST', requested_amount: review ? 900000000 : 300000000,
    term_m: 24, client_key: key,
  });
  const r1 = http.post(`${BASE}/loan/apply`, payload, { headers: { 'Content-Type': 'application/json' } });
  check(r1, { 'apply 2xx': (r) => r.status === 200 });
  const txn = r1.json('txn_ref');
  if (dup) {
    const r2 = http.post(`${BASE}/loan/apply`, payload, { headers: { 'Content-Type': 'application/json' } });
    check(r2, {
      'dup 2xx': (r) => r.status === 200,
      'dup same ref (no double-post)': (r) => r.json('txn_ref') === txn,
    });
  }
}
