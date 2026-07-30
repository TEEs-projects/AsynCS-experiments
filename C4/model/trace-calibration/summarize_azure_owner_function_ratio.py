#!/usr/bin/env python3
"""Summarize owner/application/function cardinalities in Azure Functions 2019."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import tarfile
from collections import Counter
from pathlib import Path


EXPECTED_SHA256 = "aff8b3ca7240a41a109e4ee598e0a96e45fcb92e7b8395ac19cb3748cd260d89"
DOWNLOAD_URL = (
    "https://github.com/Azure/AzurePublicDataset/releases/download/"
    "dataset-functions-2019/"
    "azurefunctions_dataset2019_azurefunctions-dataset2019.tar.xz"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def quantile(values: list[int], fraction: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def summarize(archive: Path) -> dict[str, object]:
    archive_hash = sha256(archive)
    if archive_hash != EXPECTED_SHA256:
        raise SystemExit(
            f"archive SHA-256 mismatch: expected {EXPECTED_SHA256}, got {archive_hash}"
        )

    owners: set[str] = set()
    applications: set[tuple[str, str]] = set()
    functions: set[tuple[str, str, str]] = set()
    per_day: list[dict[str, object]] = []

    with tarfile.open(archive, "r:xz") as bundle:
        names = sorted(
            name
            for name in bundle.getnames()
            if name.startswith("invocations_per_function_md.anon.d")
        )
        for name in names:
            day_owners: set[str] = set()
            day_applications: set[tuple[str, str]] = set()
            day_functions: set[tuple[str, str, str]] = set()
            source = bundle.extractfile(name)
            if source is None:
                raise SystemExit(f"missing archive member: {name}")
            rows = csv.DictReader(line.decode("utf-8") for line in source)
            for row in rows:
                owner = row["HashOwner"]
                application = row["HashApp"]
                function = row["HashFunction"]
                day_owners.add(owner)
                day_applications.add((owner, application))
                day_functions.add((owner, application, function))

            owners.update(day_owners)
            applications.update(day_applications)
            functions.update(day_functions)
            per_day.append(
                {
                    "day": name.removesuffix(".csv").rsplit(".", 1)[-1],
                    "owners": len(day_owners),
                    "applications": len(day_applications),
                    "functions": len(day_functions),
                    "functions_per_owner": len(day_functions) / len(day_owners),
                    "functions_per_application": len(day_functions)
                    / len(day_applications),
                }
            )

    functions_per_owner = Counter(owner for owner, _, _ in functions)
    applications_per_owner = Counter(owner for owner, _ in applications)
    functions_per_application = Counter((owner, app) for owner, app, _ in functions)

    return {
        "schema_version": "azure-owner-function-ratio-v1",
        "source": {
            "download_url": DOWNLOAD_URL,
            "archive_sha256": archive_hash,
            "dataset": "Azure Functions Trace 2019 revision 2",
            "selection": "union of unique HashOwner/HashApp/HashFunction tuples in d01-d14 invocation files",
        },
        "union": {
            "owners": len(owners),
            "applications": len(applications),
            "functions": len(functions),
            "functions_per_owner_mean": len(functions) / len(owners),
            "applications_per_owner_mean": len(applications) / len(owners),
            "functions_per_application_mean": len(functions) / len(applications),
            "functions_per_owner_median": statistics.median(
                functions_per_owner.values()
            ),
            "functions_per_owner_p95": quantile(
                list(functions_per_owner.values()), 0.95
            ),
            "applications_per_owner_median": statistics.median(
                applications_per_owner.values()
            ),
            "functions_per_application_median": statistics.median(
                functions_per_application.values()
            ),
        },
        "per_day": per_day,
        "model_use": {
            "cofunc_tenant_proxy": "HashOwner",
            "cofunc_tenants_t": "ceil(F / 4.928751447449084)",
            "boundary": (
                "HashOwner groups sampled applications belonging to the same Azure "
                "subscription and is a tenant proxy, not an observed CoFunc tenant. "
                "The trace contains invoked functions in a sampled application set, "
                "not every deployed function."
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = summarize(args.archive)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
