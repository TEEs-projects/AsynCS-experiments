#!/usr/bin/env python3
"""Report public C5 row and structured direct-event coverage."""

import argparse
import csv
import json
from pathlib import Path


WORKLOADS = ("dynamic-html-derived-v1", "compression-derived-random256k-level6-v1")
PROFILES = ("native-352", "asyncs-355", "reusable-358")


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = []
    for profile in PROFILES:
        for workload in WORKLOADS:
            base = args.root / profile / workload
            attempts = rows(base / "derived/c5/c5-attempts.tsv")
            summary = rows(base / "derived/c5/c5-summary.tsv")
            if len(summary) != 1:
                raise SystemExit(f"expected one summary row: {base}")
            direct = base / "direct-events/normalized-openwhisk-events.tsv"
            with direct.open(encoding="utf-8") as handle:
                event_rows = max(sum(1 for _ in handle) - 1, 0)
            validation = json.loads((base / "validation-recomputed.json").read_text())
            s = summary[0]
            records.append(
                {
                    "profile": profile,
                    "workload": workload,
                    "attempt_rows": len(attempts),
                    "summary_rows": len(summary),
                    "submitted_count": int(s["submitted_count"]),
                    "terminal_success_count": int(s["terminal_success_count"]),
                    "output_verified_count": int(s["output_verified_count"]),
                    "store_ack_count": int(s["store_ack_count"]),
                    "warm_eligible_count": int(s["warm_eligible_count"]),
                    "selected_warm_count": int(s["selected_warm_count"]),
                    "direct_event_rows": event_rows,
                    "validation_status": validation["status"],
                }
            )
    args.output.write_text(json.dumps({"schema_version": "c5-public-coverage-v1", "workloads": records}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
