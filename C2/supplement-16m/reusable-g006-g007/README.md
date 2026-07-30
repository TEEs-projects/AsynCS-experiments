# Round 377 Reusable C2 16 MiB child g006-g007

Round 377 is an immutable owner-stage formal child candidate for global groups
6 and 7. Main review is pending. It is not independently E2 or paper evidence
and must not be resumed, overwritten, topped up, or used to start another
child.

The child ran exactly two consecutive global groups. Each group contains one
genuine-fresh request followed by five immediate warm requests under one exact
action revision. All 12 logical requests reached terminal state and store,
matched RID, decrypted, and matched the workload. There were no queue-endpoint
prediction retries or failed attempts.

The exact revisions are `0.0.1@1785095597414` and
`0.0.2@1785095621059`. Groups 6 and 7 used target bindings `88` and `90`,
respectively. Both fresh requests are `CODE_INPUT/false`; all ten warm requests
are `INPUT/true` on their group's exact revision and binding. Gateway
CODE/INPUT/RESULT counts are `2/12/0`. The pre-removal captures contain one
direct `RCD400/RCD410` pair for each fresh request.

Remote-first bounded recovery retained 197 lossless direct-event occurrences
and 8 lifecycle occurrences. All required OW, RG, DB, Gateway, R, and RCD
coverage is complete. Twenty-three raw OW300 occurrences for 12 activations are
preserved without deduplication. Inventory observations (`12 -> 13` after
group 6 and `13 -> 13` after group 7) remain diagnostic environment evidence;
the accepted request-level C2 contract does not use them as a validity gate.

The existing cleanup path was invoked once without run-only group arguments
and closed the exact action `200 -> 404`; source, runner, and round writer
counts are zero.

The public tree contains only bounded non-sensitive evidence. Actual WASM,
application input, current-Gateway protected state, materialized request
bodies, full activation/result ciphertext, and verifier records remain in the
protected archive and pass byte/size/SHA verification.

The two figures are diagnostic observation QA only and are marked
`DIAGNOSTIC_COMPLETE / NOT REVIEWED`. They are not paper figures.
