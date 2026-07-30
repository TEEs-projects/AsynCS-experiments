# C1 Encoded Timing Event Contract

Status: current C1 timing contract.

This contract records request timing as boundary events first.  Phase semantics,
duration calculation, coverage, and stacked-breakdown eligibility are interpreted
after data recovery by the profile-specific dictionary and phase map.

## Main Event Table

`timing-events.tsv` is lossless structured timing data.  It must keep one row per
observed boundary event.

```text
schema_version
experiment_id
run_id
profile
concurrency
logical_request_id
attempt_id
event_code
event_seq
node
process
pid
tid
unix_ns
mono_ns
clock_domain
status
attrs_ref
```

Rules:

- Event rows do not contain component, phase, before/after, mapping relation, or
  coverage explanation.
- `profile + experiment_id + event_code` defines the event meaning through
  `event-dictionary.tsv`.
- `event_seq` is only an ordering hint within one attempt.  Duration is computed
  from the mapped event pair, not from adjacent rows.
- Same-process directly emitted spans should prefer `mono_ns`.
- Cross-process or cross-node spans use `unix_ns` and require
  `clock-sync/summary.tsv` evidence for interpretation.
- OpenWhisk activation-record timestamps copied from blocking activation
  responses are wall-clock boundary evidence.  They can define tail spans such
  as `client_tail` only when clock-sync evidence is present.
- Rows derived only from duration fields are not timing events. Do not emit
  `clock_domain=legacy_duration:*` rows in `timing-events.tsv`; do not generate
  synthetic begin/end event pairs from `attempts.tsv` duration columns. Old
  duration fields may remain in `attempts.tsv` for non-breakdown diagnostics,
  but they are outside this event contract.
- Missing required events are reported as `missing`, never as zero.
- Mechanisms that do not exist for a profile are `not_applicable`.

## Sidecar Tables

`event-dictionary.tsv`

```text
schema_version
experiment_id
profile
event_code
boundary_name
default_order
required_level
description
```

`phase-map.tsv`

```text
schema_version
experiment_id
profile
phase_name
from_event_code
to_event_code
relation
clock_rule
coverage_rule
```

`entity-map.tsv`

```text
logical_request_id
attempt_id
activation_id
rid
action_name
container_id
node
```

`event-attrs.tsv`

```text
attrs_ref
key
value
value_type
```

## Interpreter Rules

- Phase durations are calculated from `from_event_code -> to_event_code`.
- Phase maps select the clock rule. `require_unix` phases must use `unix_ns`
  even when same-process `mono_ns` values are present, and are valid only when
  clock-sync evidence is present. `require_mono_same_process` phases must share
  node, process, pid, and clock domain.
- `coarse_superset` and its child spans must not both enter the same stacked
  breakdown.
- `clock_rule=legacy_duration_ok` is not allowed in current C1 phase maps.
  A phase must be computed from observed boundary events or reported as
  `missing` / `not_applicable`.
- Duration-only DB-save markers from operational logs are diagnostics, not
  normalized timing phases. DB-save log markers may enter timing output only
  when both start and finish marker timestamps are preserved as boundary events
  such as `DB500 -> DB510`; `duration_ms` remains an attribute/diagnostic, not
  timing evidence.
- Network phases require their own frontdoor/client ingress or egress boundary
  events. Do not rename broad spans such as `C010 -> OW220` or `OW230 -> C900`
  as network time, because they also contain OpenWhisk control/queue/tail work.
- `unmeasured_gap` is not emitted as a timing event. If a report needs gap
  diagnostics, compute them outside `timing-events.tsv` and keep them out of
  component-residence stacked breakdowns.
- Optional attributes must go in `event-attrs.tsv`, not the main event schema.

## Initial Phase Vocabulary

```text
client_tail
```
