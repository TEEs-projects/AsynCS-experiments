# C3 accepted E3 v2 sources

This directory is organized by public profile, not by historical round number.
Each profile is the latest accepted E3 v2 single-batch source: seven input
sizes (1 KiB through 4 MiB), 100 requests per size, one cyclic W=1 batch,
700 submitted/terminal/output/store rows, and 699 selected warm rows.

- `asyncs/361`: accepted formal AsynCS E3 v2 profile data.
- `native/363`: accepted formal Native E3 v2 direct-event source.
- `reusable/365`: accepted formal Reusable E3 v2 profile candidate, including
  direct events and function-timing fields; it is not a paper promotion.

The old five-size sources 353/354/357/336 are superseded and are not included.
Protected request/result bytes, private verifiers, deployment logs, and figures
are excluded. Each profile retains public-safe request-level tables, direct
event tables, timing fields, contracts, provenance, and validation metadata.
