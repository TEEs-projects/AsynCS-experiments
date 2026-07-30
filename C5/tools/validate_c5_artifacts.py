#!/usr/bin/env python3
"""Validate one C5 batch package without assigning paper acceptance."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"required artifact missing or empty: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_finite_number(value: str) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return number == number and number not in (float("inf"), float("-inf"))


def recompute_same_worker_overlap_ids(rows: list[dict[str, str]]) -> set[str]:
    """Independently recompute strict overlaps from worker and client intervals."""
    intervals_by_worker: dict[str, list[tuple[str, int, int]]] = {}
    seen_ids: set[str] = set()
    for row in rows:
        activation_id = row.get("activation_id", "")
        worker = row.get("worker", "")
        if not activation_id or activation_id in seen_ids:
            raise SystemExit("low-contention attempts require unique activation IDs")
        if not worker:
            raise SystemExit(f"low-contention attempt has no worker: {activation_id}")
        try:
            begin = int(row.get("client_start_unix_ns", ""))
            end = int(row.get("client_end_unix_ns", ""))
        except ValueError as error:
            raise SystemExit(f"invalid client interval for {activation_id}") from error
        if begin < 0 or end <= begin:
            raise SystemExit(f"invalid client interval for {activation_id}")
        seen_ids.add(activation_id)
        intervals_by_worker.setdefault(worker, []).append((activation_id, begin, end))

    overlapping: set[str] = set()
    for intervals in intervals_by_worker.values():
        ordered = sorted(intervals, key=lambda value: (value[1], value[2], value[0]))
        for index, (left_id, _left_begin, left_end) in enumerate(ordered):
            for right_id, right_begin, _right_end in ordered[index + 1:]:
                if right_begin >= left_end:
                    break
                overlapping.update((left_id, right_id))
    return overlapping


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--derived-dir", required=True, type=Path)
    parser.add_argument("--figures-dir", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    attempts_path = args.derived_dir / "c5-attempts.tsv"
    summary_path = args.derived_dir / "c5-summary.tsv"
    attempts = read_rows(attempts_path)
    summaries = read_rows(summary_path)
    if len(summaries) != 1:
        raise SystemExit("c5-summary.tsv must contain exactly one data row")
    summary = summaries[0]
    expected = int(summary["expected_count"])
    selected_count = int(summary["selected_warm_count"])
    mean_ci_checks = {}
    for prefix in ("full_flow", "blocking", "workload", "wait"):
        mean = summary.get(f"{prefix}_mean_ms", "")
        low = summary.get(f"{prefix}_ci95_low_ms", "")
        high = summary.get(f"{prefix}_ci95_high_ms", "")
        mean_ci_checks[f"{prefix}_mean_present"] = is_finite_number(mean)
        mean_ci_checks[f"{prefix}_student_t_ci_valid"] = (
            selected_count < 2
            and low == ""
            and high == ""
        ) or (
            is_finite_number(mean)
            and is_finite_number(low)
            and is_finite_number(high)
            and float(low) <= float(mean) <= float(high)
        )
    checks = {
        "submitted_matches_contract": len(attempts) == expected == int(summary["submitted_count"]),
        "p0_terminal_success_complete": int(summary["terminal_success_count"]) == expected,
        "output_verification_complete": int(summary["output_verified_count"]) == expected,
        "store_ack_complete": int(summary["store_ack_count"]) == expected,
        "has_valid_warm_samples": int(summary["selected_warm_count"]) > 0,
        "request_size_fixed": summary["measured_request_bytes"].isdigit(),
        "result_size_fixed": summary["measured_result_json_bytes"].isdigit(),
        "no_sustained_queue_buildup": summary["queue_buildup_status"] != "sustained_buildup_detected",
        "materializer_gate_pass": summary["quality_gate_status"] == "pass",
        "warm_target_is_advisory": summary["warm_target_status"] in ("met", "below_target_advisory"),
        "acceptance_not_claimed": summary["acceptance_status"] == "not_reviewed",
        "latency_primary_statistic_is_mean_student_t_ci": summary.get(
            "latency_primary_statistic"
        ) == "sample_mean_with_two_sided_student_t_95_ci",
        "latency_ci_method_is_student_t": summary.get("latency_ci_method")
        == "student_t_df_n_minus_1",
        **mean_ci_checks,
    }
    if summary.get("profile") == "native" and summary.get(
        "low_contention_filter_status"
    ) == "applied":
        recomputed_overlap_ids = recompute_same_worker_overlap_ids(attempts)
        flagged_overlap_ids = {
            row["activation_id"]
            for row in attempts
            if row.get("same_worker_concurrent_request") == "true"
        }
        expected_fraction = len(recomputed_overlap_ids) / len(attempts) if attempts else 0.0
        try:
            reported_fraction = float(summary["same_worker_concurrent_excluded_fraction"])
        except (KeyError, ValueError):
            reported_fraction = float("nan")
        checks["native_worker_mapping_complete"] = (
            summary.get("worker_mapping_status")
            == "complete_activation_db_save_invoker_join"
            and all(row.get("worker", "") for row in attempts)
        )
        checks["native_overlap_flags_are_boolean"] = all(
            row.get("same_worker_concurrent_request") in {"true", "false"}
            for row in attempts
        )
        checks["native_overlap_flags_match_recomputed_intervals"] = (
            flagged_overlap_ids == recomputed_overlap_ids
        )
        checks["native_same_worker_concurrent_count_matches_recomputed"] = (
            int(summary["same_worker_concurrent_excluded_count"])
            == len(recomputed_overlap_ids)
        )
        checks["native_same_worker_concurrent_fraction_matches_recomputed"] = (
            is_finite_number(str(reported_fraction))
            and abs(reported_fraction - expected_fraction) <= 1e-12
        )
        checks["native_recomputed_overlap_rows_are_excluded"] = all(
            row.get("selected_warm") == "false"
            and row.get("sample_exclusion_reason")
            == "excluded_same_worker_concurrent_request"
            for row in attempts
            if row["activation_id"] in recomputed_overlap_ids
        )
        checks["native_nonoverlap_rows_do_not_claim_overlap_exclusion"] = all(
            row.get("sample_exclusion_reason")
            != "excluded_same_worker_concurrent_request"
            for row in attempts
            if row["activation_id"] not in recomputed_overlap_ids
        )
        checks["native_selected_rows_have_no_recomputed_overlap"] = all(
            row["activation_id"] not in recomputed_overlap_ids
            for row in attempts
            if row.get("selected_warm") == "true"
        )
        checks["native_compute_overlap_explicitly_unavailable"] = (
            summary.get("workload_compute_overlap_status")
            == "unavailable_cross_process_clock_domain"
            and summary.get("workload_compute_overlap_diagnostic_count", "") == ""
            and all(
                row.get("same_worker_workload_compute_overlap")
                == "unavailable_cross_process_clock_domain"
                for row in attempts
            )
        )
    figure_names = (
        "c5_diagnostic_timeline.csv", "c5_diagnostic_timeline.png", "c5_diagnostic_timeline.svg",
        "c5_diagnostic_statistics.csv", "c5_diagnostic_statistics.png", "c5_diagnostic_statistics.svg",
    )
    if args.figures_dir is None:
        checks["figures_not_required_for_public_export"] = True
    else:
        for name in figure_names:
            path = args.figures_dir / name
            checks[f"figure_{name}_nonempty"] = path.is_file() and path.stat().st_size > 0
    status = "pass" if all(checks.values()) else "fail"
    output = {
        "schema_version": "c5-artifact-validation-v1",
        "status": status,
        "acceptance_status": "not_reviewed",
        "artifact_classification": summary["artifact_classification"],
        "warm_sample_target_status": summary["warm_target_status"],
        "checks": checks,
        "artifacts": {
            "attempts_sha256": digest(attempts_path),
            "summary_sha256": digest(summary_path),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"C5_ARTIFACT_VALIDATION status={status} output={args.output}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
