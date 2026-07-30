# Round 379 Reusable C2 16 MiB child g010-g011

Round 379 is an immutable owner-stage formal child candidate for global groups
10 and 11. Main review is pending. It is not independently E2 or paper
evidence and must not be resumed, overwritten, topped up, or selected by
performance.

The child ran exactly two consecutive global groups. Each group contains one
genuine-fresh request followed by five immediate warm requests under one exact
action revision. All 12 logical requests reached terminal state and store,
matched RID, decrypted, and matched the workload. The first fresh logical
request used the one exact queue-endpoint prediction retry allowed by the
frozen contract; both attempts are preserved, and logical first-result latency
includes the complete retry interval.

The exact revisions are `0.0.1@1785106816794` and
`0.0.2@1785106842531`. Groups 10 and 11 used target bindings `120` and `179`,
respectively. Both fresh requests are `CODE_INPUT/false`; all ten warm requests
are `INPUT/true` on their group's exact revision and binding. Gateway
CODE/INPUT/RESULT counts are `2/12/0`. The pre-removal captures contain one
direct `RCD400/RCD410` pair for each fresh request.

Remote-first bounded recovery retained 197 lossless direct-event occurrences
and 8 lifecycle occurrences. All required OW, RG, DB, Gateway, R, and RCD
coverage is complete. Twenty-three raw OW300 occurrences for 12 terminal
activations are preserved without deduplication.

The existing cleanup path was invoked once without run-only group arguments
and closed the exact action `200 -> 404`; source, runner, and round writer
counts are zero.

The public tree contains only bounded non-sensitive evidence. Actual WASM,
application input, current-Gateway protected state, materialized request
bodies, full activation/result ciphertext, and verifier records remain in the
protected archive and pass byte/size/SHA verification.

The two figures are diagnostic observation QA only and are marked
`DIAGNOSTIC_COMPLETE / NOT REVIEWED`. They are not paper figures.
