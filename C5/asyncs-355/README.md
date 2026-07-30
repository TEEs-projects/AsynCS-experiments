# Round 355 AsynCS C5 Direct-event Replacement

This immutable public collection contains the AsynCS C5 function-warm
low-contention replacement with activation-ID-bounded OpenWhisk direct events.
It is a complete candidate pending independent main-agent review; it is not
paper evidence by itself.

## Contract

- one control and three selected workers (`.215/.217/.218`);
- four `asyncs:1` 256 MiB initial stems per worker, action concurrency 1;
- ordinary blocking/store-enabled client, global W3, p=0;
- one excluded full-output correctness probe per workload;
- one 300-request measured batch for each of `dynamic-html-derived-v1` and
  `compression-derived-random256k-level6-v1`;
- probes and measured batches use the same exact action revision
  `/guest/c5_asyncs_representative_warm_v1` `0.0.4@1784759769207`;
- primary rows are warm requests whose same-worker half-open client intervals
  `[client_start, client_end)` do not overlap any other measured request;
- the approximately 100 selected-row target is advisory.

Round 355 uses a fresh per-round KMS authority. The previous control-bound
sealed authority did not unseal on the current control lifecycle; that bounded
premeasurement failure is retained as provenance. The fresh authority passed a
stop/restart `ASYNCS_KMS_BUILD=0` unseal check before package preparation and
was frozen for both workloads outside the measured intervals. This does not
change the workload, BF-IBE/KEM profile, payload, runtime digest, store path, or
selector semantics.

## Direct Events

For every measured activation, the public package contains direct
`OW120/150/260/300/310/800` markers extracted from the controller, scheduler,
and invoker sources. All raw OW300 dispatch rows are retained; the normalized
table selects the final dispatch before OW310. No activation waitTime, total
latency, or residual was substituted for a missing event.

`FORMAL-SUMMARY.tsv` reports the sample mean with two-sided Student-t 95% CI as
the primary statistic; p50 remains diagnostic. A400/A410 are retained only as
per-request durations because cross-process monotonic clocks are not a valid
overlap domain.

## Evidence Boundary

The public package contains activation-ID/transaction-ID bounded OpenWhisk and
DB markers, structured submit/store/profile evidence, a sanitized actual
container-to-worker sidecar, derived TSVs, validators, and diagnostic PNG/SVG/CSV
figures. It excludes prepared request JSONL, BF-IBE private verifiers and skU,
full activation results, decrypted output, C_out, C_k_func, sealed state,
credentials, and broad logs.

Excluded material is retained separately under the mode-0700 protected archive
recorded in `PRIVATE-ARCHIVE-STATUS.tsv`. Its 142 source files were verified
against `PRIVATE-SHA256SUMS`; that manifest and all private bytes remain outside
Git and the public collection.
