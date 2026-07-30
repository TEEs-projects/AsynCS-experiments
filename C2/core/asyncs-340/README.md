# C2 AsynCS formal encrypted-package size grid

Round `340` is one immutable formal collection with four encrypted function-package sizes. Each size contains
40 genuine fresh exact-action placements followed immediately by five same-action warm requests, for 960 requests
in total. The data and diagnostic artifacts are complete but remain `not_reviewed` until main-agent review.

## Frozen identity

- measured top executable: `b56ec7a95006d1797a555c7ebb6c30345a675187`
- ACSC: `1826e69f84fd3bcd5f51d3307688ee667fa0ac71`
- OpenWhisk Scala: `f6bcb49866ad8a49a0427a3a0347dc0336b7550a`
- OpenWhisk C2 manifest: `8268ae3389c05786cee4cd921893a08b2ad2c2a4`
- runtime digest: `sha256:2bbaf591e3861ffa4903af8c4b53c0ffe3d8f8c68851c4d4400bef84f098e844`
- FID: `c2-asyncs-sleep50-grid-v1`
- sealed authority SHA-256: `129b90e2228ce325a093f5c59f348f1956aea57fa9dd0189eb8b214781997d3c`
- BF-IBE public parameter SHA-256: `8f59d57a63d27e0c9bf4af56becf4af39d637af856661dc9352e75103785fcd4`
- signed KMS enclave SHA-256: `a98d4950b22ca9a6de6b04e19d0b8727574d7f86ef1c0258f368009b2822cfda`

The live KMS loaded this sealed authority, unsealed the MSK, bound exactly four package labels, and generated no
fallback MSK. Provider preparation and all 160 action publishes completed before the ordinary W=1 ciphertext
submit driver entered the measured path.

## Result

All 960 requests reached terminal success and durable activation-store evidence with complete RID, decrypt,
workload, and payload checks. All 160 fresh rows pass the KMS/function-key/C_func evidence gate; all 800 warm
rows reuse their eligible fresh baseline in the same container without repeated KMS contact or C_func decrypt.
The four per-size populations are each 40 fresh plus 200 warm.

`FORMAL-SUMMARY.tsv` reports fresh/warm latency and a W=1 service-rate diagnostic defined as request count divided
by summed first-result latency. The full collection wall-clock rate was 2.001066 requests/s. Action fetch remains
`unavailable_no_direct_event`; preinitialized runtime remains `not_on_path_preinitialized_runtime`.

The remote host lacked matplotlib only after measurement, result verification, and materialization had completed.
The two diagnostic figures and validator were therefore generated locally from the same recovered derived TSVs;
no request was replayed.

## Public evidence boundary

This package includes only run/action metadata, materialized verification and timing TSVs, activation/action/RID-
bounded filtered logs, sanitized authority hashes and markers, profile/container readiness, diagnostic figures,
validators, and checksums. It excludes prepared request JSONL, private verifiers, skU, plaintext, sealed state,
complete activation JSONL/results, and broad logs.

## Cleanup

After local recovery and remote-manifest verification, the round-owned KMS was stopped, port 3000 was clear,
all 160 formal actions were absent, and no round runner remained. The remote run/public/private/preflight roots
were removed. ECS and the 3-worker AsynCS profile were not stopped; post-cleanup inventory showed four matching
runtime stems on each worker.
