# AsynCS experiment data

The AsynCS project license remains undecided.
See [AsynCS](https://github.com/TEEs-projects/AsynCS)
for the main project entry, source, workloads, build instructions, and pinned
OpenWhisk/WAMR component repositories. This data repository is
[AsynCS-experiments](https://github.com/TEEs-projects/AsynCS-experiments).

This repository is organized by the current experiment families `C1` through
`C5`. It contains accepted public-safe manifests, request-level tables,
direct-event tables, derived summaries, validators, and the explicitly
public-prepared 16 MiB contract metadata and accepted derivatives. C3 uses the accepted E3 v2 sources 361,
363, and 365; C2 Reusable 16 MiB includes the accepted G001-G017 aggregate
and the separately marked 17-row worker-stage derivative.

It does not publish E0-E5 paper artifacts, private verifiers, credentials,
private/sensitive ciphertext or result archives, cluster logs, host
inventories, or superseded/diagnostic rounds. The C2 16 MiB Asyncs entry
includes the ciphertext requests, encrypted action parameters, and action
archive authorized by its `PUBLIC-PREPARED` manifest; only private verifier,
`skU`, sealed authority state, and raw private archives are excluded. See each
family README and `COVERAGE-MATRIX.tsv` for evidence bounds.

C5 is materialized from the accepted 352 Native collection, the accepted 355
Asyncs worktree, and the 358 Reusable collection. Each has the dynamic HTML and
random 256 KiB compression workload, request/submit metadata, verification,
profile/function timing where available, store/activation events, C5 attempts
and summaries, validation metadata, and public-safe direct-event tables. The
Reusable event-occurrence tables are normalized by
`C5/tools/normalize_direct_events.py`; no raw or filtered capture logs are
included. Shared input files, expected output, event dictionary, phase map,
and hashes are under `C5/inputs/`.

The reusable C1-C3 workload contracts and selected artifacts are referenced by
the [code repository's workloads](https://github.com/TEEs-projects/AsynCS/tree/main/workloads). C1-C3
exports retain their accepted contracts and public-safe derivatives; no new
private payload archive is exposed by this repair.
