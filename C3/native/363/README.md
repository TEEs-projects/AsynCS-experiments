# Native E3 v2 round 363

One continuous Native E3 v2 batch over 1/4/16/64/256 KiB, 1 MiB, and
4 MiB. The seven sizes are cyclically interleaved 100 times at W=1.

The public collection contains normalized request, direct-event, store,
verification, materialized summary, and diagnostic figure artifacts. Actual
plaintext payloads and prepared rows remain in the protected archive. The
complete activation-result JSONL was not placed in Git. After main acceptance,
the remote prepared-request and activation-result JSONL objects were verified
against their recorded paths, bytes, and SHA-256 and then deleted exactly.
`REMOTE-CLEANUP-LEDGER.tsv` preserves that cleanup evidence.

Main independently accepted the data as
`accepted_formal_c3_e3_v2_native`. The figures are accepted as
observation/diagnostic QA artifacts only, not paper figures.
