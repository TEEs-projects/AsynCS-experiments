#!/usr/bin/env python3
"""Verify every path listed in a SHA-256 manifest of `path hash` rows."""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path

def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_sha256.py MANIFEST")
    manifest = Path(sys.argv[1])
    root = manifest.parent
    failures = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 2 or len(fields[0]) != 64:
            continue
        digest, raw_path = fields
        normalized_path = raw_path.removeprefix("./")
        path = root / normalized_path
        if not path.is_file():
            failures.append(f"missing {raw_path}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            failures.append(f"mismatch {raw_path}: {actual}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"verified {manifest}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
