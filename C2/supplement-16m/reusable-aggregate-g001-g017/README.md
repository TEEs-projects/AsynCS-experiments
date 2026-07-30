# Reusable C2 16 MiB user-closed final aggregate

This is a local, manifest-driven aggregate over immutable child collections. It
does not create a new live round and does not modify any source collection.

Main authority `04326eea1fe3dcbb6c55735e901be2fa6e5d14f8` accepts the
earliest contract-valid instance of each global group:

| Global groups | Source round |
| --- | ---: |
| 1--2 | 374 |
| 3 | 375 |
| 4--5 | 376 |
| 6--7 | 377 |
| 8--9 | 378 |
| 10--11 | 379 |
| 12--13 | 380 |
| 14--15 | 381 |
| 16--17 | 382 |

The user closed collection after group 17 because the accumulated data are
sufficient. The aggregate therefore contains 17 fresh requests, 85 immediate
warm follow-ups, and 102 unique logical request IDs. Global groups 18--40 were
not scheduled after user closure; they are not failed or missing samples.

## Files

- `children-manifest.tsv`: chronological Main-reviewed child history and
  byte-anchored action, source-session, readiness, cleanup, logical, attempt,
  public-manifest, and private-manifest provenance.
- `derived/c2/selected-logical-requests.tsv`: the 102 selected logical rows,
  with source round and source collection columns.
- `derived/c2/selected-attempts.tsv`: 107 activation attempts for those 102
  logical requests. Exact queue-prediction retries remain attempts, not extra
  samples.
- `provenance/group-source-map.tsv`: one row per selected global group with
  direct-event, lifecycle, coverage, source-manifest, action cleanup, source
  session, profile reset, public archive, and protected archive SHA links.
- `validation.json`: fail-closed aggregate validation result.

Round 374 also contains one observed attempt from its invalid group 3. That
attempt remains immutable in round 374 and contributes to
`observed_attempt_count=108`, but is not in the 107-row selected attempt
sidecar. No selection uses latency or another performance value.

The legacy round 374 source evidence predates
`SOURCE-SESSION-PROVENANCE.env`. Its immutable
`notes/source-session-launch.env` directly records the Gateway PID and
`protected_state_reused=false`; the validator binds that evidence to the
round-scoped source-session identity without editing round 374.

## Replay

From the repository root:

```bash
python3 experiments/current-scripts/C2/reusable-concurrency/validate_16m_child_aggregate.py \
  --plan experiments/current-scripts/C2/reusable-concurrency/child-group-plan-16m-v2.json \
  --children-manifest experiments/collections/c2-reusable-concurrency-16m-supplemental-final-aggregate-g001-g017-20260727/children-manifest.tsv \
  --collections-root experiments/collections \
  --user-closed-group-end 17 \
  --output <local-temp-path>```

Omitting `--user-closed-group-end` retains the original 40-group default and
must reject this 17-group prefix. No paper figure is generated here.
