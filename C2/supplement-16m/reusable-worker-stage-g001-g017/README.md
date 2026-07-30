# Reusable C2 16 MiB worker-stage direct-event derivation

Status: `owner_candidate_worker_stage_derivation_pending_main_review`.

This directory is an independent, public-safe derivation from the accepted
Reusable C2 16 MiB aggregate. It does not modify the accepted aggregate or any
source child, and it does not define a paper figure or paper narrative.

## Selection

Main authority:
`a1c2aca7d825b70dca3f47cffaee334cb58fc451`.

The source mapping is fixed by the accepted aggregate:

`g1--2=374, g3=375, g4--5=376, g6--7=377, g8--9=378,
g10--11=379, g12--13=380, g14--15=381, g16--17=382`.

For each selected fresh group, the extractor joins the accepted aggregate's
fresh row to the same activation object in that child's protected
`<protected-source>`. It then accepts exactly one
`REUSABLE_TRACE_EXECUTOR_RUN` line from `activation_get.logs`.

Selection never uses a duration or another performance value. No row is filled
from a different request, residual, cross-clock subtraction, or zero.

## Direct event boundary

- `load_ms` is `REUSABLE_TRACE_EXECUTOR_RUN.load_dur_ns / 1e6`.
- `instantiate_ms` is
  `REUSABLE_TRACE_EXECUTOR_RUN.instantiate_dur_ns / 1e6`.
- `worker_total_ms` is the exact same-row sum of those two direct durations.

These are worker-runtime WAMR load and instantiate subspans. They are not
end-to-end latency, CODE decrypt, Gateway time, or a residual.

## Result

- selected fresh coverage: `17/17`;
- groups: exactly `1--17`, one row per group;
- load arithmetic mean: `38.242349353 ms`;
- instantiate arithmetic mean: `0.344463529 ms`;
- worker-total arithmetic mean: `38.586812882 ms`.

`worker-stage-events.tsv` retains source round, group, archive path/bytes/SHA,
private-manifest path/SHA, source object/log ordinals, and a fixed selector
description. It contains no payload, ciphertext, raw trace, logical request ID,
activation ID, or container ID.

## Files

- `worker-stage-events.tsv`: 17 public-safe direct-event rows.
- `summary.json`: coverage and the three 17-row arithmetic means.
- `validation.json`: mapping, identity, direct-event, arithmetic, and
  public-safety validation.
- `PROVENANCE.env`: aggregate and tool SHA anchors.
- `MANIFEST.tsv` and `SHA256SUMS`: directory integrity.

## Replay

From the repository root, with the canonical protected collection archive
mounted at `$PROTECTED_COLLECTIONS_ROOT`:

```bash
python3 experiments/paper-artifacts/event-recovery/tools/derive_reusable_c2_16m_worker_stages.py \
  --aggregate-root experiments/collections/c2-reusable-concurrency-16m-supplemental-final-aggregate-g001-g017-20260727 \
  --public-repo-root . \
  --protected-collections-root "$PROTECTED_COLLECTIONS_ROOT" \
  --output <local-temp-path> \
  --summary <local-temp-path>
python3 experiments/paper-artifacts/event-recovery/tools/validate_reusable_c2_16m_worker_stages.py \
  --aggregate-root experiments/collections/c2-reusable-concurrency-16m-supplemental-final-aggregate-g001-g017-20260727 \
  --public-repo-root . \
  --events <local-temp-path> \
  --summary <local-temp-path> \
  --output <local-temp-path>```

The extractor still emits one row per group when a protected archive or trace
is unavailable, marks that row missing, leaves its durations empty, and exits
nonzero. The validator does not publish 17-row means for partial coverage.
