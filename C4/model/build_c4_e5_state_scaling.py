#!/usr/bin/env python3
"""Build deterministic C4 data and the current E5 key-state figure."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "generated"

FIELDS = [
    "schema_version",
    "series_id",
    "display_name",
    "evidence_type",
    "coverage",
    "functions_f",
    "warm_placements_p",
    "replicas_r",
    "tenants_t",
    "authority_secret_objects",
    "warm_secret_objects",
    "binding_objects",
    "authority_secret_bytes",
    "warm_secret_bytes",
    "binding_bytes",
    "secret_payload_bytes",
    "protected_state_payload_bytes",
    "declared_retained_storage_bytes",
    "linker_padding_bytes",
    "allocator_runtime_overhead_bytes",
    "retained_memory_bytes",
    "bytes_main_figure_eligible",
    "object_main_figure_eligible",
    "note",
]


def read_contract(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def constants(contract: dict) -> dict[str, int]:
    return {item["name"]: int(item["value"]) for item in contract["constants"]}


def placement_count(functions: int, numerator: int, denominator: int) -> int:
    return math.ceil(functions * numerator / denominator)


def build_rows(contract: dict) -> list[dict[str, object]]:
    c = constants(contract)
    rows: list[dict[str, object]] = []
    for f in contract["functions"]:
        p = placement_count(
            int(f),
            int(contract["placement_ratio_numerator"]),
            int(contract["placement_ratio_denominator"]),
        )
        r = int(contract["replicas_per_placement"])
        t = int(contract["tenant_count"])
        caps = c["asyncs_capabilities_per_placement"]
        cap_bytes = c["bfibe_private_capability_bytes"]
        fid_bytes = c["canonical_fid_bytes"]

        asyncs_authority = c["asyncs_authority_msk_bytes"]
        asyncs_warm = p * r * caps * cap_bytes
        asyncs_binding = p * r * fid_bytes
        declared = asyncs_authority + p * r * c["asyncs_bfibe_declared_storage_bytes_per_placement"]
        linker_padding = p * r * c["asyncs_bfibe_linker_padding_bytes_per_placement"]
        rows.append(
            row(
                contract,
                "asyncs-minimal-core",
                "AsynCS minimal core",
                "source-derived",
                "complete-bytes-and-objects",
                f,
                p,
                r,
                t,
                1,
                p * r * caps,
                p * r,
                asyncs_authority,
                asyncs_warm,
                asyncs_binding,
                declared,
                linker_padding,
                0,
                True,
                True,
                "One persistent MSK; two BF-IBE capabilities and one canonical FID binding per warm placement.",
            )
        )

        stored_authority = f * caps * cap_bytes
        stored_warm = p * r * caps * cap_bytes
        stored_binding = (f + p * r) * fid_bytes
        rows.append(
            row(
                contract,
                "stored-bfibe-capabilities",
                "Per-function stored capabilities",
                "paper-model",
                "complete-payload-model",
                f,
                p,
                r,
                t,
                f * caps,
                p * r * caps,
                f + p * r,
                stored_authority,
                stored_warm,
                stored_binding,
                None,
                None,
                None,
                True,
                True,
                "Same 96-byte BF-IBE capabilities and two-key obligation as AsynCS, but both capabilities are retained per function.",
            )
        )

        rows.append(
            row(
                contract,
                "wallet-paper-object-model",
                "Wallet paper model",
                "paper-model",
                "objects-only-bytes-na",
                f,
                p,
                r,
                t,
                f,
                p * r,
                f + p * r,
                None,
                None,
                None,
                None,
                None,
                None,
                False,
                True,
                "One provider private-key object per function and one copy per configured monitor; key bytes are N/A.",
            )
        )

        rows.append(
            row(
                contract,
                "cofunc-t1-paper-object-model",
                "CoFunc paper model (T=1)",
                "paper-model",
                "objects-only-bytes-na",
                f,
                p,
                r,
                t,
                t,
                p * r,
                t + p * r,
                None,
                None,
                None,
                None,
                None,
                None,
                False,
                True,
                "One tenant-key object for T=1 and one copy per active CVM placement; key bytes are N/A.",
            )
        )

        reusable_secret = p * r * c["reusable_aek_bytes"]
        reusable_binding = p * r * c["reusable_session_binding_bytes"]
        rows.append(
            row(
                contract,
                "reusable-artifact-session-lower-bound",
                "Reusable session-only lower bound",
                "source-derived",
                "partial-session-only",
                f,
                p,
                r,
                t,
                None,
                p * r,
                p * r,
                None,
                reusable_secret,
                reusable_binding,
                None,
                None,
                None,
                False,
                False,
                "Artifact AEK/session state only; missing function-key manager makes complete key-related state N/A.",
            )
        )
    return rows


def row(
    contract: dict,
    series_id: str,
    display_name: str,
    evidence_type: str,
    coverage: str,
    f: int,
    p: int,
    r: int,
    t: int,
    authority_objects: int | None,
    warm_objects: int | None,
    binding_objects: int | None,
    authority_bytes: int | None,
    warm_bytes: int | None,
    binding_bytes: int | None,
    declared_storage: int | None,
    linker_padding: int | None,
    allocator_overhead: int | None,
    bytes_eligible: bool,
    objects_eligible: bool,
    note: str,
) -> dict[str, object]:
    secret = add_optional(authority_bytes, warm_bytes)
    protected = add_optional(secret, binding_bytes)
    retained = add_optional(declared_storage, linker_padding, allocator_overhead)
    return {
        "schema_version": contract["schema_version"],
        "series_id": series_id,
        "display_name": display_name,
        "evidence_type": evidence_type,
        "coverage": coverage,
        "functions_f": f,
        "warm_placements_p": p,
        "replicas_r": r,
        "tenants_t": t,
        "authority_secret_objects": authority_objects,
        "warm_secret_objects": warm_objects,
        "binding_objects": binding_objects,
        "authority_secret_bytes": authority_bytes,
        "warm_secret_bytes": warm_bytes,
        "binding_bytes": binding_bytes,
        "secret_payload_bytes": secret,
        "protected_state_payload_bytes": protected,
        "declared_retained_storage_bytes": declared_storage,
        "linker_padding_bytes": linker_padding,
        "allocator_runtime_overhead_bytes": allocator_overhead,
        "retained_memory_bytes": retained,
        "bytes_main_figure_eligible": str(bytes_eligible).lower(),
        "object_main_figure_eligible": str(objects_eligible).lower(),
        "note": note,
    }


def add_optional(*values: int | None) -> int | None:
    if any(value is None for value in values):
        return None
    return sum(int(value) for value in values if value is not None)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for item in rows:
            writer.writerow({field: "" if item.get(field) is None else item.get(field, "") for field in fields})


def plot(rows: list[dict[str, object]], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.labelsize": 9,
        "legend.fontsize": 8,
        "svg.fonttype": "none",
        "svg.hashsalt": "asyncs-c4-e5-state-scaling-v2",
    })
    fig, axes = plt.subplots(1, 3, figsize=(14.4, 4.9), gridspec_kw={"width_ratios": [1.0, 1.0, 1.15]})
    colors = {"authority": "#C65D21", "warm": "#2F6B9A", "binding": "#8A939B"}
    schemes = ["asyncs-minimal-core", "stored-bfibe-capabilities"]
    titles = ["AsynCS minimal core\n[source-derived]", "Per-function stored capabilities\n[paper-model]"]
    for ax, scheme, title in zip(axes[:2], schemes, titles):
        selected = sorted((item for item in rows if item["series_id"] == scheme), key=lambda item: int(item["functions_f"]))
        x = [int(item["functions_f"]) for item in selected]
        authority = [int(item["authority_secret_bytes"]) for item in selected]
        warm = [int(item["warm_secret_bytes"]) for item in selected]
        binding = [int(item["binding_bytes"]) for item in selected]
        ax.stackplot(x, authority, warm, binding, colors=[colors["authority"], colors["warm"], colors["binding"]], alpha=0.9)
        ax.plot(x, [a + w + b for a, w, b in zip(authority, warm, binding)], color="#20252A", marker="o", markersize=3.5, linewidth=1.2)
        ax.set_xscale("log")
        ax.set_xlim(1, 10000)
        ax.set_ylim(bottom=0)
        ax.set_title(title, loc="left")
        ax.set_xlabel("Protected functions F (P=ceil(0.25F), R=1)")
        ax.grid(axis="y", color="#D8DDE2", linewidth=0.7)
        ax.spines[["top", "right"]].set_visible(False)
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        endpoint = selected[-1]
        ax.annotate(
            f"{int(endpoint['protected_state_payload_bytes']) / 1_000_000:.2f} MB",
            (int(endpoint["functions_f"]), int(endpoint["protected_state_payload_bytes"])),
            xytext=(-8, 7), textcoords="offset points", ha="right", fontsize=8, color="#20252A",
        )
    axes[0].set_ylabel("Protected-state payload bytes")
    axes[0].annotate("persistent MSK = 32 B", (2.2, 30000), fontsize=8, color=colors["authority"])

    object_styles = [
        ("asyncs-minimal-core", "AsynCS", "#2F6B9A", "o", "-"),
        ("stored-bfibe-capabilities", "Stored capabilities", "#C65D21", "s", "-"),
        ("wallet-paper-object-model", "Wallet (bytes N/A)", "#7A4E9D", "^", "--"),
        ("cofunc-t1-paper-object-model", "CoFunc T=1 (bytes N/A)", "#5C7A29", "D", ":"),
    ]
    ax = axes[2]
    for scheme, label, color, marker, linestyle in object_styles:
        selected = sorted((item for item in rows if item["series_id"] == scheme), key=lambda item: int(item["functions_f"]))
        x = [int(item["functions_f"]) for item in selected]
        y = [int(item["authority_secret_objects"]) + int(item["warm_secret_objects"]) for item in selected]
        ax.plot(x, y, color=color, marker=marker, markersize=4, linewidth=1.5, linestyle=linestyle, label=label)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1, 10000)
    ax.set_title("Secret-object count\n[granularity differs by scheme]", loc="left")
    ax.set_xlabel("Protected functions F (P=ceil(0.25F), R=1)")
    ax.set_ylabel("Authority + warm secret objects")
    ax.grid(color="#D8DDE2", linewidth=0.7, which="both")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper left")

    composition_handles = [
        Line2D([0], [0], color=colors["authority"], linewidth=7, label="Authority long-lived key state"),
        Line2D([0], [0], color=colors["warm"], linewidth=7, label="Warm placement key copies"),
        Line2D([0], [0], color=colors["binding"], linewidth=7, label="Necessary key/FID binding state"),
    ]
    fig.legend(handles=composition_handles, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.39, 1.01))
    fig.suptitle("E5: Key-related protected-state scaling", x=0.02, y=1.055, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.02, -0.01, "Deterministic C4 model. Policy, labels not retained for key selection, code, request payloads, and sealing/time costs are excluded. Wallet/CoFunc bytes remain N/A; Reusable session-only state is not plotted as a complete total.", fontsize=8, color="#41484F")
    fig.tight_layout(rect=[0, 0.04, 1, 0.91])
    svg = output_dir / "e5_key_related_protected_state.svg"
    png = output_dir / "e5_key_related_protected_state.png"
    creator = "C4/E5 deterministic state-scaling generator"
    fig.savefig(svg, bbox_inches="tight", metadata={"Date": None, "Creator": creator})
    fig.savefig(png, dpi=180, bbox_inches="tight", metadata={"Software": creator})
    plt.close(fig)
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
    return svg, png


def write_constants(contract: dict, path: Path) -> None:
    write_csv(path, ["name", "value", "unit", "evidence_type", "source_id"], contract["constants"])


def write_coverage(rows: list[dict[str, object]], path: Path) -> None:
    seen: set[str] = set()
    output: list[dict[str, object]] = []
    for item in rows:
        if str(item["series_id"]) in seen:
            continue
        seen.add(str(item["series_id"]))
        output.append({key: item[key] for key in ["series_id", "display_name", "evidence_type", "coverage", "bytes_main_figure_eligible", "object_main_figure_eligible", "note"]})
    write_csv(path, list(output[0]), output)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(output_dir: Path, artifacts: list[tuple[Path, str]]) -> None:
    rows = []
    for path, description in artifacts:
        rows.append({"artifact": path.relative_to(ROOT).as_posix(), "sha256": sha256(path), "bytes": path.stat().st_size, "description": description})
    write_csv(output_dir / "manifest.csv", ["artifact", "sha256", "bytes", "description"], rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=HERE / "model_contract.json")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    contract = read_contract(args.contract)
    rows = build_rows(contract)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = args.output_dir / "c4_e5_state_scaling.csv"
    const = args.output_dir / "c4_e5_constants.csv"
    coverage = args.output_dir / "c4_e5_baseline_coverage.csv"
    write_csv(data, FIELDS, rows)
    write_constants(contract, const)
    write_coverage(rows, coverage)
    svg, png = plot(rows, args.output_dir)
    write_manifest(args.output_dir, [
        (data, "deterministic C4 state rows"),
        (const, "model constants and evidence classes"),
        (coverage, "baseline completeness and N/A boundaries"),
        (svg, "current E5 main figure, vector"),
        (png, "current E5 main figure, raster"),
    ])
    print(f"C4_E5_STATE_SCALING_OK rows={len(rows)} output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
