# C5 low-contention direct-event sources

This family contains the latest accepted structured evidence from three
independent profile roots:

- `native-352`: Native collection 352
- `asyncs-355`: accepted Asyncs worktree collection 355
- `reusable-358`: Reusable collection 358

Each root contains `dynamic-html-derived-v1` and
`compression-derived-random256k-level6-v1`. The workload directories retain
measured request/submit metadata, verification, profile/function timing when
the source provides it, store and activation events, `c5-attempts.tsv`,
`c5-summary.tsv`, validation metadata, and structured direct-event coverage.
Reusable direct-event occurrences are exported as
`direct-events/normalized-openwhisk-events.tsv` with deployment paths and IPs
removed while preserving event fields. Native also retains its source-named
`openwhisk-event-occurrences.tsv` alongside the normalized release table.

`inputs/` contains the shared dynamic HTML fixture, template, exact expected
output, random 256 KiB binary, workload contract, event dictionary, phase map,
and `INPUT-SHA256SUMS.tsv`. `tools/` contains the minimum C5 summary builder,
validator, and direct-event normalizer needed to inspect this export.

Raw and filtered logs, host inventories, private verifier/key material,
ciphertext archives, credentials, and deployment provenance are excluded.
The 355 source calls its validation artifact `validation-summary.json`; that
name is retained rather than inferred from the 352/358 layout.
