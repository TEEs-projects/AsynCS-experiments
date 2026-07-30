#!/usr/bin/env python3
"""Copy a structured direct-event table while removing deployment provenance."""

import argparse
import csv
import re
from pathlib import Path


IPV4 = re.compile(r"(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])")
PRIVATE_PATH = re.compile(r"/(?:data/work|root|home)/[^\t\n]*")


def public_value(value: str, field: str) -> str:
    if field in {"source_path", "source_log"}:
        return "<structured-source>"
    value = PRIVATE_PATH.sub("<protected-source>", value)
    value = value.replace("release-source", "release-source")
    value = value.replace("release-worktree", "release-worktree")
    value = value.replace("RELEASE_WORKSPACE", "RELEASE_WORKSPACE")
    return IPV4.sub("<deployment-ip>", value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    with args.input.open(newline="") as source:
        reader = csv.DictReader(source, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("input has no header")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=reader.fieldnames, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            for row in reader:
                writer.writerow({key: public_value(value or "", key) for key, value in row.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
