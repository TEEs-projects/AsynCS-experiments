# Round 358 Reusable C5 function-warm direct-event replacement

This immutable collection repeats the accepted round 343 request contract while
adding activation-ID-bounded direct event evidence. It contains one 300-request
W3 batch for each frozen C5 workload. Primary rows are warm, terminal, verified,
stored requests that do not strictly overlap another measured client interval
on the same worker. Cross-worker concurrency remains valid.

Every measured activation has direct C010/C800/C900, OW120/OW150/OW260/OW300/
OW310/OW800, N300/N700/N800, RG270/RG280, GINPUT, R400/R410/R420/R430 and
DB500/DB510 evidence. RF400/RF410 are also complete. Raw OW300 duplicate
occurrences are retained. No missing boundary is zero-filled, inferred from a
residual, or subtracted across clocks.

Raw WASM, protected envelopes, request bodies, activation/result ciphertext and
verifier state remain under the protected canonical `<protected-source> archive and are
excluded from Git. `PRIVATE-ARCHIVE-MANIFEST.tsv` records their byte identities.
The figures are diagnostic QA, not paper figures. Main-agent acceptance remains
pending.
