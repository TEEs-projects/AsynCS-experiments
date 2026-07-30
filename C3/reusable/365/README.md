# Round 365 Reusable E3 v2 bounded handoff

Round 365 is accepted by the main agent as
`accepted_formal_reusable_e3_v2_profile_candidate`. This classification accepts
the Reusable profile collection; it does not promote its diagnostic figures or
any paper artifact.

## Measurement boundary

- Contract: seven cyclic sizes, 100 requests per size, 700 total, W=1.
- Submitted and terminal: 700/700.
- RID/decrypt/full-output verification and CouchDB store closure: 700/700.
- Warm-selected requests: 699; the first cold request remains in the raw and
  diagnostic tables but is excluded from the warm analysis.
- Retry and top-up: zero measured retries and no top-up.
- Gateway CODE/INPUT/RESULT: 1/700/0 with zero status failures.
- Exact action cleanup: HTTP 200 -> DELETE 200 -> HTTP 404.

The same-authority excluded 4 MiB probe ran before the formal root and is not
part of these counts. It used the same FQEN, exact revision, FID, code-envelope
SHA, and current-Gateway source session as the measured batch. Its first
activation attempt hit the accepted exact queue-endpoint prediction condition;
the single permitted immediate retry completed with terminal, full-output,
RID/decrypt, DB, Gateway, R/RF, and RG closure.

Main-agent classification:
`accepted_formal_reusable_e3_v2_profile_candidate`.

`ARTIFACT-VALIDATION.json` remains byte-frozen at the owner-stage gate. Its
`acceptance_status=not_reviewed` and owner proposal record the state before
independent main review; they do not reverse the main-agent acceptance recorded
in this README and `COLLECTION-STATUS.md`.

## Direct evidence

`recovery/derived/event-occurrences.tsv` contains 27,301 direct occurrences.
All 700 activations have the required C010/C800/C900, OW120/150/260/300/310/800,
N300/700/800, RG270/280, GINPUT, R400/410, RF400/410, R420/430, DB500/510,
Invoker/container/WAMR, and profile markers. The 1,398 OW300 occurrences cover
700 distinct activations and retain 698 duplicates losslessly. No missing event
is filled with zero, inferred from residuals, or subtracted across clocks.

The two figure families under `figures/e3-v2-reusable-owner-candidate/` are
owner diagnostic QA only. They are not paper figures and remain `not_reviewed`.

## Archive boundary

The Git-visible root contains bounded source lines, structured evidence,
validation, manifests, and diagnostic figures. The protected archive is stored
outside Git at:

`<private-source-root>/experiments/collections/365_c3-reusable-concurrency-e3-v2-seven-size-single-batch-same-authority-replacement`

It retains the seven plaintext payloads and manifest, verifier, source
authority, request mapping, and exact action-cleanup bodies. Six large remote
objects are intentionally omitted from the bounded transfer after event
extraction; `OMITTED-REMOTE-OBJECTS.tsv` records each path, byte count, SHA-256,
and reason. This includes repeated protected packs, the complete activation
documents, and large request material, not event evidence.

`REMOTE-BOUNDED-SHA256SUMS` verifies the exact remote bounded handoff. Its
original remote `PUBLIC-MANIFEST.tsv` is preserved byte-for-byte at
`provenance/remote-bounded/PUBLIC-MANIFEST.tsv` so it cannot be confused with
the final owner manifest at the collection root; the recorded remote hash is
unchanged. `SHA256SUMS` verifies the final Git-visible owner package.
`PRIVATE-SHA256SUMS` verifies the protected local archive and is public only as
a hash inventory; the referenced private bytes are excluded from Git.
