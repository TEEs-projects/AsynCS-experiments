# C2 16 MiB supplement

`asyncs-370` contains the public ciphertext payloads listed by its authoritative
`PUBLIC-PREPARED-SHA256SUMS`: `action-default-params.json`, `action.zip`, and
`requests.jsonl`, together with their manifests and bindings. The payloads
contain encrypted values and public metadata only; private verifier material,
`skU`, and sealed authority state are excluded.

`reusable-aggregate-g001-g017` is the accepted user-closed aggregate for
groups G001-G017, mapped to rounds 374-382: 17 fresh plus 85 immediate warm
requests, 102 logical requests and 107 selected attempts.

`reusable-worker-stage-g001-g017` is the already-derived 17-row worker-stage
table for the same groups. Its local validation passes, but its handoff
classification remains `pending_main_review`; it is included with that
explicit status and must not be described as an accepted headline result.

The accepted child-group derivatives remain available for audit. Ciphertext
result archives, private verifiers, credentials, and raw deployment logs are
excluded. Public ciphertext payloads are included; private verifier/`skU`
material is excluded.
