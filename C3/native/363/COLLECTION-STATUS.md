# C3 E3 v2 Native round 363

- Measurement status: `complete`
- Acceptance status: `accepted_formal_c3_e3_v2_native`
- Main data classification: `accepted_formal_c3_e3_v2_native`
- Artifact classification: `accepted_observation_diagnostic_qa_only`
- Sample organization: one continuous 700-request cyclic batch, W=1
- Size schedule: 1/4/16/64/256 KiB, 1 MiB, 4 MiB; 100 requests per size
- Queue retry/top-up: `0 / none`
- Measured interval: `2026-07-24T19:18:22.780166Z` through
  `2026-07-24T19:20:45.205889Z`

All 700 requests reached terminal success and passed complete output,
activation GET, CouchDB, C010/C800/C900, N400/N410, and
OW120/150/260/300/310/800 checks. One initial request has positive
`initTime`; the other 699 warm requests are selected.

The local SSH control connection broke after the measured process had started.
The sole remote writer continued to the immutable 700/700 terminal boundary.
No second request process, retry, or top-up was started. Recovery reattached
only to the existing 700 activation IDs and produced complete direct-event and
store evidence.

The two repeated large JSONL objects were not copied into the public
collection. Before cleanup, both remote paths were rechecked against the
recorded bytes and SHA-256. Main acceptance then authorized their exact
deletion; `REMOTE-CLEANUP-LEDGER.tsv` records the result. Prepared rows, the
seven actual plaintext payloads, and their manifest remain protected locally
and checksum-verified. All bounded public events and joined verification
evidence remain in this collection.

Main independently checked the public and private checksums, all 700 joined
requests, all 13 required event families, the 699 selected warm requests, and
the original figures. The timeline/statistics PNG and SVG files are accepted
as observation/diagnostic QA artifacts only; they are not paper figures.
