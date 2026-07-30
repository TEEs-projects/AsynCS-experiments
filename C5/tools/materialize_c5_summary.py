#!/usr/bin/env python3
"""Join one C5 ordinary-client batch into per-request and summary tables."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from pathlib import Path
from typing import Any

from scipy.stats import t as student_t_distribution


ATTEMPT_FIELDS = [
    "profile", "workload_id", "ordinal", "logical_request_id", "activation_id",
    "terminal_success", "output_verified", "store_acknowledged", "warm_eligible",
    "warm_reason", "selected_warm", "same_worker_concurrent_request",
    "same_worker_workload_compute_overlap", "sample_exclusion_reason",
    "container_identity", "worker", "init_time_ms",
    "activation_wait_time_ms", "http_request_bytes", "http_response_bytes",
    "client_start_unix_ns", "client_end_unix_ns", "db_finish_unix_ns",
    "blocking_latency_ms", "full_flow_latency_ms", "workload_duration_ms",
    "function_duration_ms", "application_input_bytes", "application_output_bytes",
    "application_output_sha256", "result_json_bytes", "verification_status",
]
SUMMARY_FIELDS = [
    "schema_version", "profile", "workload_id", "expected_count", "submitted_count",
    "terminal_success_count", "output_verified_count", "store_ack_count", "warm_eligible_count",
    "init_excluded_count", "selected_warm_count", "target_warm_samples", "warm_target_status",
    "low_contention_filter_status", "worker_mapping_status",
    "same_worker_concurrent_excluded_count", "same_worker_concurrent_excluded_fraction",
    "workload_compute_overlap_status", "workload_compute_overlap_diagnostic_count",
    "unique_warm_container_count", "measured_request_bytes", "measured_result_json_bytes",
    "latency_primary_statistic", "latency_ci_method",
    "full_flow_mean_ms", "full_flow_ci95_low_ms", "full_flow_ci95_high_ms",
    "full_flow_p50_ms", "full_flow_p95_ms", "blocking_p50_ms", "blocking_p95_ms",
    "blocking_mean_ms", "blocking_ci95_low_ms", "blocking_ci95_high_ms",
    "workload_mean_ms", "workload_ci95_low_ms", "workload_ci95_high_ms",
    "workload_p50_ms", "workload_p95_ms", "wait_p50_ms", "wait_p95_ms",
    "wait_mean_ms", "wait_ci95_low_ms", "wait_ci95_high_ms",
    "wait_first_quartile_p50_ms", "wait_last_quartile_p50_ms", "queue_buildup_status",
    "completion_rate_per_sec", "quality_gate_status", "artifact_classification", "acceptance_status",
]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def mean_student_t_ci95(values: list[float]) -> tuple[float | str, float | str, float | str]:
    if not values:
        return "", "", ""
    mean = statistics.fmean(values)
    if len(values) < 2:
        return mean, "", ""
    standard_error = statistics.stdev(values) / math.sqrt(len(values))
    critical = float(student_t_distribution.ppf(0.975, len(values) - 1))
    margin = critical * standard_error
    return mean, mean - margin, mean + margin


def as_bool(value: str) -> bool:
    return value.lower() == "true"


def strict_overlap_members(intervals: list[tuple[str, int, int]]) -> set[str]:
    """Return every request participating in a strict interval overlap."""
    overlapping: set[str] = set()
    ordered = sorted(intervals, key=lambda value: (value[1], value[2], value[0]))
    if any(begin < 0 or end <= begin for _, begin, end in ordered):
        raise SystemExit("invalid request interval")
    for index, (left_id, left_begin, left_end) in enumerate(ordered):
        for right_id, right_begin, right_end in ordered[index + 1:]:
            if right_begin >= left_end:
                break
            if left_begin < right_end and right_begin < left_end:
                overlapping.update((left_id, right_id))
    return overlapping


def unique_by_activation_id(rows: list[dict[str, str]], label: str) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        activation_id = row.get("activation_id", "")
        if not activation_id or activation_id in indexed:
            raise SystemExit(f"{label} activation IDs must be present and unique")
        indexed[activation_id] = row
    return indexed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--workload-id", required=True)
    parser.add_argument("--expected-count", required=True, type=int)
    parser.add_argument("--target-warm-samples", default=1000, type=int)
    parser.add_argument("--measured-request-json-bytes", required=True, type=int)
    parser.add_argument("--measured-result-json-bytes", required=True, type=int)
    parser.add_argument("--attempts", required=True, type=Path)
    parser.add_argument("--verification", required=True, type=Path)
    parser.add_argument("--store-evidence", required=True, type=Path)
    parser.add_argument("--low-contention-filter", action="store_true")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    if args.expected_count <= 0 or args.target_warm_samples <= 0:
        raise SystemExit("expected and target counts must be positive")
    if args.low_contention_filter and args.profile != "native":
        raise SystemExit("this Native materializer only supports low-contention filtering for profile=native")

    attempts = read_tsv(args.attempts)
    verification = read_tsv(args.verification)
    store = read_tsv(args.store_evidence)
    if args.low_contention_filter:
        unique_by_activation_id(attempts, "attempt")
        verification_by_id = unique_by_activation_id(verification, "verification")
        store_by_id = unique_by_activation_id(store, "store evidence")
    else:
        verification_by_id = {row["activation_id"]: row for row in verification}
        store_by_id = {row["activation_id"]: row for row in store}
    rows: list[dict[str, Any]] = []
    for attempt in attempts:
        activation_id = attempt["activation_id"]
        verified = verification_by_id.get(activation_id, {})
        stored = store_by_id.get(activation_id, {})
        client_start = int(attempt["client_start_unix_ns"])
        client_end = int(attempt["client_end_unix_ns"])
        db_finish = int(stored["db_finish_unix_ns"]) if stored.get("db_finish_unix_ns") else 0
        terminal = as_bool(attempt["terminal_success"]) and verified.get("terminal_success") == "true"
        output_ok = verified.get("output_verified") == "true"
        store_ok = stored.get("store_status") == "put_acknowledged"
        warm = verified.get("warm_eligible") == "true"
        verification_ok = verified.get("verification_status") == "ok"
        selected = terminal and output_ok and store_ok and warm and verification_ok
        rows.append(
            {
                "profile": args.profile,
                "workload_id": args.workload_id,
                "ordinal": attempt["ordinal"],
                "logical_request_id": attempt["logical_request_id"],
                "activation_id": activation_id,
                "terminal_success": str(terminal).lower(),
                "output_verified": str(output_ok).lower(),
                "store_acknowledged": str(store_ok).lower(),
                "warm_eligible": str(warm).lower(),
                "warm_reason": verified.get("warm_reason", "missing_verification"),
                "selected_warm": str(selected).lower(),
                "same_worker_concurrent_request": "unavailable",
                "same_worker_workload_compute_overlap": "unavailable",
                "sample_exclusion_reason": "",
                "container_identity": verified.get("container_identity", ""),
                "worker": "",
                "init_time_ms": verified.get("init_time_ms", ""),
                "activation_wait_time_ms": verified.get("activation_wait_time_ms", ""),
                "http_request_bytes": attempt["http_request_bytes"],
                "http_response_bytes": attempt["http_response_bytes"],
                "client_start_unix_ns": client_start,
                "client_end_unix_ns": client_end,
                "db_finish_unix_ns": db_finish,
                "blocking_latency_ms": (client_end - client_start) / 1_000_000,
                "full_flow_latency_ms": (db_finish - client_start) / 1_000_000 if db_finish else "",
                "workload_duration_ms": int(verified["workload_duration_ns"]) / 1_000_000 if verified.get("workload_duration_ns") else "",
                "function_duration_ms": int(verified["function_duration_ns"]) / 1_000_000 if verified.get("function_duration_ns") else "",
                "application_input_bytes": verified.get("application_input_bytes", ""),
                "application_output_bytes": verified.get("application_output_bytes", ""),
                "application_output_sha256": verified.get("application_output_sha256", ""),
                "result_json_bytes": verified.get("result_json_bytes", ""),
                "verification_status": verified.get("verification_status", "missing_verification"),
            }
        )

    filter_status = "not_requested"
    worker_mapping_status = "not_requested"
    workload_compute_overlap_status = "not_requested"
    concurrent_request_ids: set[str] = set()
    if args.low_contention_filter:
        intervals_by_worker: dict[str, list[tuple[str, int, int]]] = {}
        for row in rows:
            activation_id = str(row["activation_id"])
            worker = store_by_id.get(activation_id, {}).get("node", "")
            if not worker:
                raise SystemExit(f"missing DB-save invoker identity for {activation_id}")
            row["worker"] = worker
            intervals_by_worker.setdefault(worker, []).append(
                (
                    activation_id,
                    int(row["client_start_unix_ns"]),
                    int(row["client_end_unix_ns"]),
                )
            )
        for intervals in intervals_by_worker.values():
            concurrent_request_ids.update(strict_overlap_members(intervals))
        for row in rows:
            concurrent = str(row["activation_id"]) in concurrent_request_ids
            row["same_worker_concurrent_request"] = str(concurrent).lower()
            row["same_worker_workload_compute_overlap"] = (
                "unavailable_cross_process_clock_domain"
            )
            if concurrent:
                row["sample_exclusion_reason"] = "excluded_same_worker_concurrent_request"
                row["selected_warm"] = "false"
        filter_status = "applied"
        worker_mapping_status = "complete_activation_db_save_invoker_join"
        workload_compute_overlap_status = "unavailable_cross_process_clock_domain"

    selected = [row for row in rows if row["selected_warm"] == "true"]
    full_flow = [float(row["full_flow_latency_ms"]) for row in selected]
    blocking = [float(row["blocking_latency_ms"]) for row in selected]
    workload = [float(row["workload_duration_ms"]) for row in selected]
    waits = [float(row["activation_wait_time_ms"]) for row in selected]
    full_flow_mean, full_flow_ci_low, full_flow_ci_high = mean_student_t_ci95(full_flow)
    blocking_mean, blocking_ci_low, blocking_ci_high = mean_student_t_ci95(blocking)
    workload_mean, workload_ci_low, workload_ci_high = mean_student_t_ci95(workload)
    wait_mean, wait_ci_low, wait_ci_high = mean_student_t_ci95(waits)
    quartile_size = max(1, len(waits) // 4) if waits else 0
    first_wait = waits[:quartile_size] if quartile_size else []
    last_wait = waits[-quartile_size:] if quartile_size else []
    first_wait_p50 = statistics.median(first_wait) if first_wait else 0.0
    last_wait_p50 = statistics.median(last_wait) if last_wait else 0.0
    if len(waits) < 20:
        queue_status = "insufficient_for_trend"
    elif last_wait_p50 > max(first_wait_p50 * 2, first_wait_p50 + 5.0):
        queue_status = "sustained_buildup_detected"
    else:
        queue_status = "no_sustained_buildup"
    completion_times = sorted(int(row["db_finish_unix_ns"]) for row in selected)
    completion_rate = 0.0
    if len(completion_times) > 1 and completion_times[-1] > completion_times[0]:
        completion_rate = (len(completion_times) - 1) * 1_000_000_000 / (
            completion_times[-1] - completion_times[0]
        )
    request_sizes = {int(row["http_request_bytes"]) for row in rows}
    result_sizes = {
        int(row["result_json_bytes"])
        for row in rows
        if str(row["result_json_bytes"]).isdigit()
    }
    quality_pass = (
        len(rows) == args.expected_count
        and sum(row["terminal_success"] == "true" for row in rows) == args.expected_count
        and sum(row["output_verified"] == "true" for row in rows) == args.expected_count
        and sum(row["store_acknowledged"] == "true" for row in rows) == args.expected_count
        and bool(selected)
        and request_sizes == {args.measured_request_json_bytes}
        and result_sizes == {args.measured_result_json_bytes}
        and queue_status != "sustained_buildup_detected"
    )
    summary = {
        "schema_version": "c5-summary-v1",
        "profile": args.profile,
        "workload_id": args.workload_id,
        "expected_count": args.expected_count,
        "submitted_count": len(rows),
        "terminal_success_count": sum(row["terminal_success"] == "true" for row in rows),
        "output_verified_count": sum(row["output_verified"] == "true" for row in rows),
        "store_ack_count": sum(row["store_acknowledged"] == "true" for row in rows),
        "warm_eligible_count": sum(row["warm_eligible"] == "true" for row in rows),
        "init_excluded_count": sum(row["warm_eligible"] != "true" for row in rows),
        "selected_warm_count": len(selected),
        "target_warm_samples": args.target_warm_samples,
        "warm_target_status": "met" if len(selected) >= args.target_warm_samples else "below_target_advisory",
        "low_contention_filter_status": filter_status,
        "worker_mapping_status": worker_mapping_status,
        "same_worker_concurrent_excluded_count": len(concurrent_request_ids),
        "same_worker_concurrent_excluded_fraction": (
            len(concurrent_request_ids) / len(rows) if rows else 0.0
        ),
        "workload_compute_overlap_status": workload_compute_overlap_status,
        "workload_compute_overlap_diagnostic_count": "",
        "unique_warm_container_count": len({row["container_identity"] for row in selected}),
        "measured_request_bytes": next(iter(request_sizes)) if len(request_sizes) == 1 else "mixed",
        "measured_result_json_bytes": next(iter(result_sizes)) if len(result_sizes) == 1 else "mixed",
        "latency_primary_statistic": "sample_mean_with_two_sided_student_t_95_ci",
        "latency_ci_method": "student_t_df_n_minus_1",
        "full_flow_mean_ms": full_flow_mean,
        "full_flow_ci95_low_ms": full_flow_ci_low,
        "full_flow_ci95_high_ms": full_flow_ci_high,
        "full_flow_p50_ms": percentile(full_flow, 0.50),
        "full_flow_p95_ms": percentile(full_flow, 0.95),
        "blocking_mean_ms": blocking_mean,
        "blocking_ci95_low_ms": blocking_ci_low,
        "blocking_ci95_high_ms": blocking_ci_high,
        "blocking_p50_ms": percentile(blocking, 0.50),
        "blocking_p95_ms": percentile(blocking, 0.95),
        "workload_mean_ms": workload_mean,
        "workload_ci95_low_ms": workload_ci_low,
        "workload_ci95_high_ms": workload_ci_high,
        "workload_p50_ms": percentile(workload, 0.50),
        "workload_p95_ms": percentile(workload, 0.95),
        "wait_mean_ms": wait_mean,
        "wait_ci95_low_ms": wait_ci_low,
        "wait_ci95_high_ms": wait_ci_high,
        "wait_p50_ms": percentile(waits, 0.50),
        "wait_p95_ms": percentile(waits, 0.95),
        "wait_first_quartile_p50_ms": first_wait_p50,
        "wait_last_quartile_p50_ms": last_wait_p50,
        "queue_buildup_status": queue_status,
        "completion_rate_per_sec": completion_rate,
        "quality_gate_status": "pass" if quality_pass else "fail",
        "artifact_classification": "diagnostic_candidate",
        "acceptance_status": "not_reviewed",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(args.output_dir / "c5-attempts.tsv", ATTEMPT_FIELDS, rows)
    write_tsv(args.output_dir / "c5-summary.tsv", SUMMARY_FIELDS, [summary])
    print(
        "C5_SUMMARY_READY "
        f"workload={args.workload_id} submitted={len(rows)} selected_warm={len(selected)} "
        f"queue={queue_status} status={summary['quality_gate_status']}"
    )
    return 0 if quality_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
