# C3 E3 v2 AsynCS round 361

- Measurement status: `complete`
- Acceptance status: `accepted_formal_asyncs_e3_v2_profile_candidate`
- Owner classification: `complete_valid_asyncs_e3_v2_candidate`
- Main-agent classification: `accepted_formal_asyncs_e3_v2_profile_candidate`
- Artifact role: accepted AsynCS E3 v2 profile candidate for later cross-profile assembly
- Sample organization: one continuous 700-request batch, W=1
- Size schedule: 1/4/16/64/256 KiB, 1 MiB, 4 MiB; cyclic 100 times
- Queue retry limit: 0
- Measured interval: `2026-07-24T02:46:13.707716Z` through
  `2026-07-24T02:56:31.281562Z`

All 700 requests completed successfully, with exactly 100 requests per size.
Full-output verification, activation GET result identity, CouchDB persistence,
shared/profile timing, and the required OpenWhisk direct-event chain are
complete for all requests. The first request is warm-ineligible; the remaining
699 valid warm requests are selected.

The root became immutable with the first measured request. No request was
appended, relaunched, or retried. Diagnostic figures are QA artifacts and are
not paper figures or accepted paper evidence by themselves. Their generated
manifest fields remain `not_reviewed` to preserve that artifact boundary.

Independent main-agent review confirmed 700/700 terminal/output/activation
GET/store/shared/profile/OpenWhisk evidence, exactly 100 requests per size,
the cyclic ordinal schedule with `W=1` and retry zero, all 47 public checksums,
all 107 protected-private checksums, and both diagnostic figures without
cropping, overlap, or an evident metric-boundary error.

After public and protected-private checksums closed, only the exact remote 361
root was deleted. The KMS, action, 5-invoker/40-stem profile, and ECS cluster
were left running for the coordinator.
