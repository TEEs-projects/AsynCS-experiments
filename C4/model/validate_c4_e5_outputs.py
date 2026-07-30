#!/usr/bin/env python3
"""Validate committed C4/E5 data and figure artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "generated"
GENERATED_ARTIFACTS = [
    "c4_e5_state_scaling.csv",
    "c4_e5_constants.csv",
    "c4_e5_baseline_coverage.csv",
    "e5_key_related_protected_state.svg",
    "e5_key_related_protected_state.png",
]

SPEC = importlib.util.spec_from_file_location("c4_e5", HERE / "build_c4_e5_state_scaling.py")
assert SPEC and SPEC.loader
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_data(output_dir: Path) -> None:
    data_path = output_dir / "c4_e5_state_scaling.csv"
    with data_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == MODEL.FIELDS, reader.fieldnames
        rows = list(reader)
    assert len(rows) == 25
    assert {int(row["functions_f"]) for row in rows} == {1, 10, 100, 1000, 10000}
    assert {row["series_id"] for row in rows} == {
        "asyncs-minimal-core",
        "stored-bfibe-capabilities",
        "wallet-paper-object-model",
        "cofunc-t1-paper-object-model",
        "reusable-artifact-session-lower-bound",
    }

    for row in rows:
        f = int(row["functions_f"])
        assert int(row["warm_placements_p"]) == (f + 3) // 4
        assert row["replicas_r"] == "1"
        byte_fields = [
            "authority_secret_bytes",
            "warm_secret_bytes",
            "binding_bytes",
            "secret_payload_bytes",
            "protected_state_payload_bytes",
        ]
        if row["bytes_main_figure_eligible"] == "true":
            assert all(row[field] != "" for field in byte_fields)
            assert int(row["secret_payload_bytes"]) == int(row["authority_secret_bytes"]) + int(row["warm_secret_bytes"])
            assert int(row["protected_state_payload_bytes"]) == int(row["secret_payload_bytes"]) + int(row["binding_bytes"])
        else:
            assert row["protected_state_payload_bytes"] == ""

    asyncs = [row for row in rows if row["series_id"] == "asyncs-minimal-core"]
    assert {row["authority_secret_objects"] for row in asyncs} == {"1"}
    assert {row["authority_secret_bytes"] for row in asyncs} == {"32"}
    assert [int(row["protected_state_payload_bytes"]) for row in asyncs] == [256, 704, 5632, 56032, 560032]


def validate_evidence() -> None:
    evidence = read_csv(HERE / "source_evidence.csv")
    by_id = {row["source_id"]: row for row in evidence}
    assert len(by_id) == len(evidence)
    contract = MODEL.read_contract(HERE / "model_contract.json")
    for constant in contract["constants"]:
        source = by_id[constant["source_id"]]
        assert source["evidence_type"] == constant["evidence_type"]
        if source["evidence_type"] in {"source-derived", "artifact-measured"}:
            assert len(source["sha256"]) == 64, source["source_id"]


def validate_manifest(output_dir: Path) -> None:
    manifest = read_csv(output_dir / "manifest.csv")
    assert [Path(row["artifact"]).name for row in manifest] == GENERATED_ARTIFACTS
    for row in manifest:
        path = output_dir / Path(row["artifact"]).name
        assert path.is_file()
        assert digest(path) == row["sha256"]
        assert path.stat().st_size == int(row["bytes"])


def validate_figure(output_dir: Path) -> None:
    svg = output_dir / "e5_key_related_protected_state.svg"
    root = ET.parse(svg).getroot()
    text = " ".join(part.strip() for part in root.itertext() if part.strip())
    for label in [
        "Key-related protected-state scaling",
        "AsynCS minimal core",
        "Per-function stored capabilities",
        "Wallet (bytes N/A)",
        "CoFunc T=1 (bytes N/A)",
        "Necessary key/FID binding state",
        "Reusable session-only state is not plotted",
    ]:
        assert label in text, label
    svg_source = svg.read_text(encoding="utf-8")
    assert "dc:date" not in svg_source
    assert all(line == line.rstrip() for line in svg_source.splitlines())

    png = output_dir / "e5_key_related_protected_state.png"
    header = png.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", header[16:24])
    assert width >= 2000 and height >= 800, (width, height)
    assert png.stat().st_size > 100_000


def validate_determinism() -> None:
    with tempfile.TemporaryDirectory(prefix=".c4-e5-a-", dir=HERE) as a_name, tempfile.TemporaryDirectory(prefix=".c4-e5-b-", dir=HERE) as b_name:
        a = Path(a_name)
        b = Path(b_name)
        command = ["python3", str(HERE / "build_c4_e5_state_scaling.py"), "--output-dir"]
        subprocess.run([*command, str(a)], check=True, capture_output=True, text=True)
        subprocess.run([*command, str(b)], check=True, capture_output=True, text=True)
        for name in GENERATED_ARTIFACTS:
            assert digest(a / name) == digest(b / name), name


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check-determinism", action="store_true")
    args = parser.parse_args()
    validate_data(args.output_dir)
    validate_evidence()
    validate_manifest(args.output_dir)
    validate_figure(args.output_dir)
    if args.check_determinism:
        validate_determinism()
    print(f"C4_E5_OUTPUTS_VALID rows=25 deterministic={args.check_determinism}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
