# Round 360 Reusable C2 formal collection candidate

Round 360 is the sole request-level Reusable-concurrency C2 formal run allocated
after immutable diagnostic rounds 342, 346, 347, and 359. It uses one action
name and a continuous exact-revision chain across four artifact sizes. Each of
160 revisions contributes one fresh request followed immediately by five warm
requests, for 960 logical requests.

The runner reached terminal success for 960/960 logical requests. All 160 fresh
rows satisfy exact revision authority, `CODE_INPUT`, and `warmed=false`; all 800
warm rows use the same revision and positive target binding as their fresh row
and satisfy `INPUT`, `warmed=true`. Terminal response, CouchDB store, RID,
direct-result decryption, workload output, and Gateway `RESULT=0` close for all
rows. One exact queue-endpoint prediction race was retried once under the
frozen contract; the logical first-result latency spans the first attempt start
through the final terminal end.

`recovery/direct-events/event-occurrences.tsv` retains every direct occurrence
from the activation-ID/Gateway-line bounded sources. It contains 15,359 rows,
including all 1,759 raw `OW300` occurrences for 960 activations. The separate
single-boundary compatibility view selects the first `OW300` occurrence per
activation only for the legacy materializer. No event is deduplicated in the
lossless table, zero-filled, reconstructed from a residual, or joined across
clock domains.

The legacy materializer labels its two figures `diagnostic_complete` because
they are QA artifacts, not paper figures. Its validator passes the complete
960-row formal contract. Owner classification is
`formal_c2_request_level_direct_events_candidate_pending_main_review`; only the
main agent may accept or reject the formal collection.

Actual request and result ciphertext, verifier state, fresh current-Gateway
source state, byte-exact WASM, and application inputs remain under the ignored
`private/` boundary. Public Git content contains only bounded filtered evidence,
structured tables, QA figures, hashes, and non-sensitive provenance.

The measured action
`c2-reusable-360-request-level-direct-events_revision_rotation` was deleted by
the existing profile cleanup path and verified HTTP `200 -> 404`. Cluster
lifecycle remains owned by the main coordinator.
