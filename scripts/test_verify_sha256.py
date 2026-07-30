#!/usr/bin/env python3
"""Minimal regression test for manifest paths beginning with './'."""
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    verifier = Path(__file__).with_name("verify_sha256.py")
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        dotfile = root / ".gitignore"
        dotfile.write_text("ignored-example\n", encoding="utf-8")
        digest = hashlib.sha256(dotfile.read_bytes()).hexdigest()
        manifest = root / "SHA256SUMS"
        manifest.write_text(f"{digest}  ./.gitignore\n", encoding="utf-8")
        subprocess.run([sys.executable, str(verifier), str(manifest)], check=True)
    print("dotfile ./ prefix regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
