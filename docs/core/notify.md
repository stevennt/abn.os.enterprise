# Notification fan-out v1.0 (issue #56) — status pushes are the visible SLA

## Provider abstraction

One interface, three drivers; flows call `notify(template_id, recipient, vars)` and
never touch a provider SDK. Driver order per recipient preference, then fallback:

```
preferred (push) -> fallback-1 (Zalo OA) -> fallback-2 (SMS) -> DLQ (bank.dlq, A04)
```

Each attempt is idempotent (same `notification_id` = instance+step+template; A07)
and consent-checked first (E47 receipt for the channel — no receipt, no send,
logged as suppressed). Provider outage degrades channel-by-channel, never silently.

## Template registry pointer

Templates live in `templates/` (registry `templates/registry.yaml`, track H77):
versioned VI copy, per-channel length variants, consent-gate flags. This issue sets
the contract; H77 seeds the first 10 templates. Sending an unregistered template id
is a deploy-blocking error (CI asserts registry membership for every template id
cited in flows — track H).
