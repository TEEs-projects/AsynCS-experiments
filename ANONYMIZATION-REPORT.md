# Anonymization report

Status: clear for the final pre-commit scans; `gitleaks` was not available locally.

The export retains public-safe event fields, request-level tables, and
public-prepared-manifest-authorized ciphertext payloads while excluding
private/sensitive payload archives, credentials, raw logs, host inventories,
private archives, and external symlinks. The final deterministic scan covers
480 files.
The required private provenance marker count is 0; non-loopback IPs, key
material, external symlinks, nested Git directories, and credential values are
0. One mixed-case four-character substring inside a long opaque ciphertext/
digest JSON value was classified as data rather than a host marker. `gitleaks` was unavailable
locally. Machine-readable findings are in `anonymization-findings.json`;
unresolved high-risk findings: 0.
