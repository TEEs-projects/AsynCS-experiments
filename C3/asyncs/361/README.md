# Round 361 E3 v2 AsynCS

This immutable public collection is the AsynCS E3 v2 formal candidate. It
contains one continuous W=1 batch of 700 ordinary blocking/store-enabled
requests: seven deterministic ASCII identity sizes in cyclic order, repeated
100 times.

The public package contains structured client, profile, CouchDB, and
activation-ID-bounded OpenWhisk evidence; normalized direct events; derived
attempt and size summaries; validators; and two diagnostic QA figures. It does
not contain prepared ciphertext request JSONL, payload bytes, private
verifiers, `skU`, sealed KMS state, complete activation results, or broad logs.
Those experiment inputs and private verification results remain in the
mode-0700 archive identified by `PRIVATE-ARCHIVE-STATUS.tsv`.

Owner-side gates pass. Independent main-agent review accepts this collection as
`accepted_formal_asyncs_e3_v2_profile_candidate`. The timeline and statistics
figures remain diagnostic QA artifacts, not paper figures; their generated
artifact manifests retain `not_reviewed`.
