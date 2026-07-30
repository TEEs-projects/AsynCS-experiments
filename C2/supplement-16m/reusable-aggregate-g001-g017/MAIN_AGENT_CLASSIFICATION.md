# Reusable C2 16 MiB final aggregate main-agent classification

Classification:
`accepted_user_closed_final_aggregate_groups_g001_g017`.

The user ended live collection after global group 17 and declared the
accumulated data sufficient. This aggregate therefore contains 17 fresh
requests, 85 warm follow-ups, and 102 unique logical request IDs. Global
groups 18--40 were not scheduled after that decision and are neither failed
nor missing samples.

The selected source mapping is:

- groups 1--2: round 374;
- group 3: round 375;
- groups 4--5: round 376;
- groups 6--7: round 377;
- groups 8--9: round 378;
- groups 10--11: round 379;
- groups 12--13: round 380;
- groups 14--15: round 381;
- groups 16--17: round 382.

Each mapping selects the earliest Main-accepted contract-valid instance. No
latency or other performance value participates in selection. The aggregate
contains 107 selected attempts for the 102 logical samples; contract-authorized
queue prediction retries remain in the attempt sidecar. Round 374 contains one
additional observed attempt from its invalid group 3, so the immutable child
history contains 108 observed attempts without adding a selected sample.

Independent Main review confirmed:

- aggregate `SHA256SUMS`: 9/9 PASS;
- byte-exact replay with `--user-closed-group-end 17`: PASS;
- 17 group/source rows and nine immutable child sources;
- the original 40-group default rejects this prefix as expected;
- the focused 16 MiB test and ordinary Reusable C2 regression: PASS.

The owner-stage `validation.json` and `LOCAL-VALIDATION-STATUS.env` retain
their generation-time `not_reviewed`/`pending` fields. This classification is
the later Main review authority and does not rewrite the checksummed aggregate
bytes.

The aggregate is accepted as the durable Reusable C2/E2 16 MiB supplemental
data source. It generates no paper figure and does not determine paper layout.
