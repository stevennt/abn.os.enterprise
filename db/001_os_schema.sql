-- OS system-of-record schema v1.0 (issue #55) — Supabase Postgres, schema `ops`.
-- Beside the event log (D36): log is truth of what happened, these tables are
-- queryable state. Apply with `psql $OPS_DB < db/001_os_schema.sql`.
create schema if not exists ops;

create table ops.instances (
  id text primary key,
  flow_id text not null, flow_version text not null,
  event_type text not null, idempotency_key text not null unique,
  state text not null default 'RUNNING', -- RUNNING|DONE|HELD|FAILED
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table ops.steps (
  instance_id text not null references ops.instances(id) on delete cascade,
  step_id text not null, seq int not null,
  kind text not null, owner_role text not null, level text not null,
  outcome text, decided_at timestamptz,
  primary key (instance_id, step_id)
);
create table ops.tasks (
  id text primary key, instance_id text not null references ops.instances(id) on delete cascade,
  step_id text not null, role_queue text not null, assignee text,
  sla_due timestamptz not null, state text not null default 'OPEN',
  decision text, decided_at timestamptz
);
create table ops.rule_versions (
  rule_id text not null, version text not null,
  pack text not null, released_at timestamptz not null default now(),
  is_default boolean not null default false,
  primary key (rule_id, version)
);
create table ops.audit (
  id text primary key, instance_id text not null, seq int not null,
  step_id text not null, actor text not null,
  rule_version text, model_version text,
  decision text, ts bigint not null,
  hash_prev text not null, hash text not null,
  unique (instance_id, seq)
);
-- RLS sketch (enable per table; owners see own instances, auditors read-only):
-- alter table ops.instances enable row level security;
-- create policy owner_read on ops.instances for select using (
--   id in (select instance_id from ops.case_participants where user_id = auth.uid()));
-- create policy auditor_read on ops.instances for select to auditor using (true);
-- create policy no_anon on ops.instances for all to anon using (false);
-- Service role bypasses RLS (gateway mints scoped JWTs per F54; anon has zero access).
