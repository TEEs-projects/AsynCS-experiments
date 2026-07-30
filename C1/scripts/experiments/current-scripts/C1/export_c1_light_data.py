#!/usr/bin/env python3
"""Create a lossless structured local-transfer tree for C1 collection rounds.

"Light" means raw log noise is removed, not that samples are aggregated or
downsampled.  This exporter copies per-run/per-request/per-attempt structured
tables and preserves materialized per-marker extracted TSVs.  When marker logs
are available, it can also materialize the same extracted TSVs so local recovery
does not need to rsync large node logs by default.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


SELECTED_RUN_FILES = {
    "RUN-CONFIG.md",
    "action-cleanup.log",
    "asyncs-prewarm-summary.tsv",
    "asyncs-request-payloads.tsv",
    "attempts.tsv",
    "boundary-quality.tsv",
    "entity-map.tsv",
    "event-attrs.tsv",
    "logical-requests.tsv",
    "placements.tsv",
    "phase-coverage.tsv",
    "phase-durations.tsv",
    "phase-summary.tsv",
    "premeasure-settle.tsv",
    "premeasure-warmup.tsv",
    "retry-stats.tsv",
    "run-config.json",
    "run-metadata.json",
    "startup-observations.tsv",
    "timing-events.tsv",
}

SELECTED_TOP_LEVEL_DATA_DIRS = {
    "asyncs-marker-runtime-probe",
    "native-marker-runtime-probe",
    "openwhisk-marker-runtime-probe",
    "profile-logs",
}

INVOKER_DB_SAVE_START_RE = re.compile(
    r"^\[(?P<ts>[^\]]+)\].*\[#(?P<tid>[^\]]+)\].*saving document: 'id: guest/(?P<activation_id>[^,']+).*database_saveDocument_start"
)
INVOKER_DB_SAVE_FINISH_RE = re.compile(
    r"^\[(?P<ts>[^\]]+)\].*\[#(?P<tid>[^\]]+)\].*database_saveDocument_finish:[^:\]]+:(?P<dur_ms>[0-9.]+)"
)
REUSABLE_EXECUTOR_SUMMARY_RE = re.compile(r"REUSABLE_TRACE_EXECUTOR_RUN (?P<fields>.*)$")
REUSABLE_EXECUTOR_RESULT_LOGICAL_RE = re.compile(
    r'logical_request_id": String\("(?P<logical_request_id>[^"]+)"\)'
)
REUSABLE_EXECUTOR_RESULT_ATTEMPT_RE = re.compile(r'attempt_id": Number\((?P<attempt_id>\d+)\)')
REUSABLE_TRACE_FIELD_RE = re.compile(r"(\w+)=([^ ]*)")
REUSABLE_TRACE_FIELDS = [
    "reset_runtime_dur_ns",
    "load_dur_ns",
    "instantiate_dur_ns",
    "create_exec_env_dur_ns",
    "lookup_start_dur_ns",
    "call_function_dur_ns",
    "run_total_dur_ns",
    "container_id",
    "wasm_bytes",
    "input_bytes",
    "result_bytes",
    "status",
]
C1_TIMING_EVENT_RE = re.compile(r"C1TIMING_EVENT\|(?P<fields>.*)$")
C1_TIMING_FIELD_RE = re.compile(r"([^=|]+)=([^|]*)")
INTERNAL_RESCHEDULE_INJECTION_RE = re.compile(
    r"(?:(?P<inner_log>/[^:\s]+):)?\[(?P<timestamp>[^\]]+)\].*C1_INTERNAL_RESCHEDULE_INJECTION\|(?P<fields>.*)$"
)
INTERNAL_RESCHEDULE_INJECTION_FIELDS = [
    "activation_id",
    "node",
    "invoker",
    "timestamp",
    "timestamp_unix_ns",
    "container_id",
    "reason",
    "status",
    "source_log",
    "line",
    "inner_log",
    "raw_line",
]
SCHEDULER_DISPATCH_FIELDS = [
    "activation_id",
    "transaction_id",
    "delivery_path",
    "event_instance_index",
    "node",
    "process",
    "pid",
    "tid",
    "unix_ns",
    "mono_ns",
    "clock_domain",
    "source_log",
    "line",
]
OPENWHISK_CONTROLLER_EVENT_FIELDS = [
    "activation_id",
    "event_code",
    "boundary_name",
    "transaction_id",
    "node",
    "producer_node",
    "process",
    "pid",
    "tid",
    "unix_ns",
    "mono_ns",
    "clock_domain",
    "source_log",
    "line",
]
NATIVE_WORKER_BOUNDARY_FIELDS = [
    "activation_id",
    "event_code",
    "boundary_name",
    "event_instance_index",
    "node",
    "process",
    "pid",
    "tid",
    "unix_ns",
    "mono_ns",
    "clock_domain",
    "source_log",
    "line",
    "container_id",
    "target_container_id",
    "reschedule_reason",
    "retry_index",
]
OPENWHISK_WORKER_BOUNDARY_FIELDS = NATIVE_WORKER_BOUNDARY_FIELDS

NGINX_FRONTDOOR_FIELDS = [
    "run_id",
    "logical_request_id",
    "attempt_id",
    "system",
    "request_id",
    "status",
    "request",
    "node",
    "source_log",
    "line",
    "msec",
    "request_time",
    "upstream_response_time",
    "upstream_connect_time",
    "upstream_header_time",
    "upstream_addr",
    "upstream_status",
    "connection",
    "connection_requests",
    "log_format_version",
    "start_unix_ns",
    "finish_unix_ns",
]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def parse_trace_fields(text: str) -> dict[str, str]:
    return {match.group(1): match.group(2) for match in REUSABLE_TRACE_FIELD_RE.finditer(text)}


def parse_c1_timing_fields(text: str) -> dict[str, str]:
    return {match.group(1): match.group(2) for match in C1_TIMING_FIELD_RE.finditer(text)}


def iso_timestamp_to_unix_ns(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    parsed = parsed.astimezone(timezone.utc)
    return str(int(parsed.timestamp()) * 1_000_000_000 + parsed.microsecond * 1_000)


def decimal_seconds_to_unix_ns(value: str) -> int | None:
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    return int(parsed * Decimal(1_000_000_000))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_file(src: Path, dst: Path, manifest: list[dict[str, str]], output_root: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    manifest.append(
        {
            "relative_path": dst.relative_to(output_root).as_posix(),
            "bytes": str(dst.stat().st_size),
            "sha256": sha256_file(dst),
        }
    )


def copy_file_unmanifested(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def count_tsv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return max(0, sum(1 for _ in handle) - 1)


def iter_run_dirs(data_root: Path) -> list[Path]:
    if not data_root.exists():
        return []
    run_dirs: list[Path] = []
    for profile_dir in sorted(path for path in data_root.iterdir() if path.is_dir()):
        for run_dir in sorted(path for path in profile_dir.iterdir() if path.is_dir()):
            if (run_dir / "attempts.tsv").exists() or (run_dir / "run-config.json").exists():
                run_dirs.append(run_dir)
    return run_dirs


def copy_existing_extracted(run_dir: Path, dst_run_dir: Path) -> dict[str, int]:
    copied: dict[str, int] = {}
    extracted_dir = run_dir / "extracted"
    if not extracted_dir.exists():
        return copied
    for src in sorted(extracted_dir.glob("*.tsv")):
        dst = dst_run_dir / "extracted" / src.name
        copy_file_unmanifested(src, dst)
        copied[src.name] = count_tsv_rows(dst)
    return copied


def copy_clock_sync(run_dir: Path, dst_run_dir: Path, manifest: list[dict[str, str]], output_root: Path) -> list[str]:
    copied: list[str] = []
    clock_sync_dir = run_dir / "clock-sync"
    if not clock_sync_dir.exists():
        return copied
    for src in sorted(clock_sync_dir.glob("*.tsv")):
        dst = dst_run_dir / "clock-sync" / src.name
        copy_file(src, dst, manifest, output_root)
        copied.append(src.name)
    return copied


def copy_selected_tree(src_dir: Path, dst_dir: Path, manifest: list[dict[str, str]], output_root: Path) -> int:
    copied = 0
    if not src_dir.exists():
        return copied
    for src in sorted(path for path in src_dir.rglob("*") if path.is_file()):
        rel = src.relative_to(src_dir)
        copy_file(src, dst_dir / rel, manifest, output_root)
        copied += 1
    return copied


def copy_top_level_diagnostics(data_root: Path, output_root: Path, manifest: list[dict[str, str]]) -> dict[str, int]:
    copied_counts: dict[str, int] = {}
    for dirname in sorted(SELECTED_TOP_LEVEL_DATA_DIRS):
        count = copy_selected_tree(data_root / dirname, output_root / dirname, manifest, output_root)
        if count:
            copied_counts[dirname] = count
    return copied_counts


def read_run_metadata(run_dir: Path) -> dict[str, object]:
    path = run_dir / "run-metadata.json"
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            parsed = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def structured_log_label(path: Path, role: str, run_metadata: dict[str, object]) -> str:
    stem = path.stem[:-len(".c1timing")] if path.stem.endswith(".c1timing") else path.stem
    if role in {"controller", "scheduler"}:
        control_node = run_metadata.get("control_node")
        return str(control_node) if control_node else stem
    invoker_prefix = "invoker-"
    if role == "invoker" and stem.startswith(invoker_prefix):
        return stem[len(invoker_prefix):]
    return stem


def iter_timing_event_logs(run_dir: Path, role: str) -> list[tuple[Path, str]]:
    structured_dir = run_dir / "structured-timing-events"
    structured_patterns = {
        "controller": ("controller*.c1timing.log",),
        "scheduler": ("scheduler*.c1timing.log",),
        "invoker": ("invoker*.c1timing.log",),
    }
    structured_logs: list[Path] = []
    for pattern in structured_patterns[role]:
        structured_logs.extend(sorted(structured_dir.glob(pattern)))
    if structured_logs:
        run_metadata = read_run_metadata(run_dir)
        return [
            (path, structured_log_label(path, role, run_metadata))
            for path in sorted(set(structured_logs))
        ]

    return [
        (path, path.parent.name)
        for path in sorted((run_dir / "nodes").glob(f"*/{role}.log"))
    ]


def extract_activation_db_save(run_dir: Path, dst_run_dir: Path) -> int:
    attempts_path = run_dir / "attempts.tsv"
    if not attempts_path.exists():
        return 0
    activation_ids = {
        row.get("activation_id", "")
        for row in read_tsv(attempts_path)
        if row.get("activation_id")
    }
    if not activation_ids:
        return 0

    rows: list[dict[str, str]] = []
    emitted: set[str] = set()
    for log_path in sorted((run_dir / "nodes").glob("*/invoker.log")):
        pending_by_tid: dict[str, tuple[str, int, str, str]] = {}
        node = log_path.parent.name
        with log_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                start_match = INVOKER_DB_SAVE_START_RE.search(line)
                if start_match:
                    pending_by_tid[start_match.group("tid")] = (
                        start_match.group("activation_id"),
                        line_no,
                        start_match.group("ts"),
                        iso_timestamp_to_unix_ns(start_match.group("ts")),
                    )
                    continue
                finish_match = INVOKER_DB_SAVE_FINISH_RE.search(line)
                if finish_match is None:
                    continue
                pending = pending_by_tid.pop(finish_match.group("tid"), None)
                if pending is None:
                    continue
                activation_id, start_line, start_time_utc, start_unix_ns = pending
                if activation_id not in activation_ids or activation_id in emitted:
                    continue
                finish_time_utc = finish_match.group("ts")
                finish_unix_ns = iso_timestamp_to_unix_ns(finish_time_utc)
                emitted.add(activation_id)
                rows.append(
                    {
                        "activation_id": activation_id,
                        "duration_ms": finish_match.group("dur_ms"),
                        "node": node,
                        "tid": finish_match.group("tid"),
                        "start_time_utc": start_time_utc,
                        "finish_time_utc": finish_time_utc,
                        "start_unix_ns": start_unix_ns,
                        "finish_unix_ns": finish_unix_ns,
                        "source_log": log_path.relative_to(run_dir).as_posix(),
                        "start_line": str(start_line),
                        "finish_line": str(line_no),
                    }
                )
    if rows:
        write_tsv(
            dst_run_dir / "extracted" / "activation-db-save.tsv",
            [
                "activation_id",
                "duration_ms",
                "node",
                "tid",
                "start_time_utc",
                "finish_time_utc",
                "start_unix_ns",
                "finish_unix_ns",
                "source_log",
                "start_line",
                "finish_line",
            ],
            rows,
        )
    return len(rows)


def extract_nginx_frontdoor(run_dir: Path, dst_run_dir: Path) -> int:
    attempts_path = run_dir / "attempts.tsv"
    if not attempts_path.exists():
        return 0
    attempt_keys = {
        (row.get("logical_request_id", ""), row.get("attempt_id", ""))
        for row in read_tsv(attempts_path)
        if row.get("logical_request_id") and row.get("attempt_id")
    }
    if not attempt_keys:
        return 0
    rows: list[dict[str, str]] = []
    emitted: set[tuple[str, str]] = set()
    for log_path in sorted((run_dir / "nodes").glob("*/nginx-access.log")):
        node = log_path.parent.name
        with log_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                line = line.rstrip("\n")
                if line.startswith("C1TIMINGV2|"):
                    parts = line.split("|", 16)
                    if len(parts) != 17:
                        continue
                    (
                        _prefix,
                        msec,
                        request_time,
                        upstream_response_time,
                        upstream_connect_time,
                        upstream_header_time,
                        upstream_addr,
                        upstream_status,
                        connection,
                        connection_requests,
                        request_id,
                        run_id,
                        system,
                        logical_request_id,
                        attempt_id,
                        status,
                        request,
                    ) = parts
                    log_format_version = "c1_timing_v2"
                elif line.startswith("C1TIMING|"):
                    parts = line.split("|", 11)
                    if len(parts) != 12:
                        continue
                    (
                        _prefix,
                        msec,
                        request_time,
                        upstream_response_time,
                        upstream_connect_time,
                        request_id,
                        run_id,
                        system,
                        logical_request_id,
                        attempt_id,
                        status,
                        request,
                    ) = parts
                    upstream_header_time = ""
                    upstream_addr = ""
                    upstream_status = ""
                    connection = ""
                    connection_requests = ""
                    log_format_version = "c1_timing_v1"
                else:
                    continue
                key = (logical_request_id, attempt_id)
                if key not in attempt_keys or key in emitted:
                    continue
                finish_ns = decimal_seconds_to_unix_ns(msec)
                request_time_ns = decimal_seconds_to_unix_ns(request_time)
                if finish_ns is None or request_time_ns is None:
                    continue
                start_ns = finish_ns - request_time_ns
                if start_ns <= 0 or finish_ns < start_ns:
                    continue
                emitted.add(key)
                rows.append(
                    {
                        "run_id": run_id,
                        "logical_request_id": logical_request_id,
                        "attempt_id": attempt_id,
                        "system": system,
                        "request_id": request_id,
                        "status": status,
                        "request": request,
                        "node": node,
                        "source_log": log_path.relative_to(run_dir).as_posix(),
                        "line": str(line_no),
                        "msec": msec,
                        "request_time": request_time,
                        "upstream_response_time": upstream_response_time,
                        "upstream_connect_time": upstream_connect_time,
                        "upstream_header_time": upstream_header_time,
                        "upstream_addr": upstream_addr,
                        "upstream_status": upstream_status,
                        "connection": connection,
                        "connection_requests": connection_requests,
                        "log_format_version": log_format_version,
                        "start_unix_ns": str(start_ns),
                        "finish_unix_ns": str(finish_ns),
                    }
                )
    if rows:
        write_tsv(
            dst_run_dir / "extracted" / "nginx-frontdoor.tsv",
            NGINX_FRONTDOOR_FIELDS,
            rows,
        )
    return len(rows)


def extract_reusable_executor(run_dir: Path, dst_run_dir: Path) -> int:
    attempts_path = run_dir / "attempts.tsv"
    if not attempts_path.exists():
        return 0
    attempt_keys = {
        (row.get("logical_request_id", ""), row.get("attempt_id", ""))
        for row in read_tsv(attempts_path)
        if row.get("logical_request_id") and row.get("attempt_id")
    }
    if not attempt_keys:
        return 0

    rows: list[dict[str, str]] = []
    emitted: set[tuple[str, str]] = set()
    for log_path in sorted((run_dir / "nodes").glob("*/executor.log")):
        pending: list[tuple[int, dict[str, str]]] = []
        node = log_path.parent.name
        with log_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                summary_match = REUSABLE_EXECUTOR_SUMMARY_RE.search(line)
                if summary_match:
                    pending.append((line_no, parse_trace_fields(summary_match.group("fields"))))
                    continue
                logical_match = REUSABLE_EXECUTOR_RESULT_LOGICAL_RE.search(line)
                if logical_match is None or not pending:
                    continue
                attempt_match = REUSABLE_EXECUTOR_RESULT_ATTEMPT_RE.search(line)
                attempt_id = attempt_match.group("attempt_id") if attempt_match else "1"
                key = (logical_match.group("logical_request_id"), attempt_id)
                summary_line, fields = pending.pop()
                if key not in attempt_keys or key in emitted:
                    continue
                emitted.add(key)
                row = {
                    "logical_request_id": key[0],
                    "attempt_id": key[1],
                    "node": node,
                    "source_log": log_path.relative_to(run_dir).as_posix(),
                    "summary_line": str(summary_line),
                    "result_line": str(line_no),
                }
                for field in REUSABLE_TRACE_FIELDS:
                    row[field] = fields.get(field, "")
                rows.append(row)
    if rows:
        write_tsv(
            dst_run_dir / "extracted" / "reusable-executor-run.tsv",
            [
                "logical_request_id",
                "attempt_id",
                "node",
                "source_log",
                "summary_line",
                "result_line",
                *REUSABLE_TRACE_FIELDS,
            ],
            rows,
        )
    return len(rows)


def extract_openwhisk_scheduler_dispatch(run_dir: Path, dst_run_dir: Path) -> int:
    return extract_openwhisk_scheduler_event(
        run_dir,
        dst_run_dir,
        event_code="OW300",
        output_name="openwhisk-scheduler-dispatch.tsv",
    )


def extract_openwhisk_activation_queue_enter(run_dir: Path, dst_run_dir: Path) -> int:
    return extract_openwhisk_scheduler_event(
        run_dir,
        dst_run_dir,
        event_code="OW260",
        output_name="openwhisk-activation-queue-enter.tsv",
    )


def extract_openwhisk_controller_events(run_dir: Path, dst_run_dir: Path) -> int:
    attempts_path = run_dir / "attempts.tsv"
    if not attempts_path.exists():
        return 0
    activation_ids = {
        row.get("activation_id", "")
        for row in read_tsv(attempts_path)
        if row.get("activation_id")
    }
    if not activation_ids:
        return 0

    rows: list[dict[str, str]] = []
    emitted: set[tuple[str, str]] = set()
    for log_path, node in iter_timing_event_logs(run_dir, "controller"):
        if not node:
            continue
        with log_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                match = C1_TIMING_EVENT_RE.search(line)
                if match is None:
                    continue
                fields = parse_c1_timing_fields(match.group("fields"))
                event_code = fields.get("event_code", "")
                if event_code not in {"OW120", "OW150"}:
                    continue
                activation_id = fields.get("activation_id", "")
                key = (activation_id, event_code)
                if activation_id not in activation_ids or key in emitted:
                    continue
                if not fields.get("unix_ns"):
                    continue
                emitted.add(key)
                rows.append(
                    {
                        "activation_id": activation_id,
                        "event_code": event_code,
                        "boundary_name": fields.get("boundary_name", ""),
                        "transaction_id": fields.get("transaction_id", ""),
                        "node": node,
                        "producer_node": fields.get("node", ""),
                        "process": fields.get("process", "openwhisk_controller"),
                        "pid": fields.get("pid", ""),
                        "tid": fields.get("tid", ""),
                        "unix_ns": fields.get("unix_ns", ""),
                        "mono_ns": fields.get("mono_ns", ""),
                        "clock_domain": fields.get("clock_domain", "openwhisk_controller_jvm_mono"),
                        "source_log": log_path.relative_to(run_dir).as_posix(),
                        "line": str(line_no),
                    }
                )
    if rows:
        write_tsv(
            dst_run_dir / "extracted" / "openwhisk-controller-events.tsv",
            OPENWHISK_CONTROLLER_EVENT_FIELDS,
            rows,
        )
    return len(rows)


def extract_openwhisk_scheduler_event(
    run_dir: Path,
    dst_run_dir: Path,
    *,
    event_code: str,
    output_name: str,
) -> int:
    attempts_path = run_dir / "attempts.tsv"
    if not attempts_path.exists():
        return 0
    activation_ids = {
        row.get("activation_id", "")
        for row in read_tsv(attempts_path)
        if row.get("activation_id")
    }
    if not activation_ids:
        return 0

    rows: list[dict[str, str]] = []
    event_instance_counts: dict[tuple[str, str], int] = {}
    # Reusable-original uses the classic load balancer inside the controller JVM,
    # so OW260/OW300 can be emitted from controller.log rather than scheduler.log.
    # Prefer scheduler logs when they contain current-run rows; fall back to
    # controller logs only when scheduler extraction produced nothing.
    for role in ("scheduler", "controller"):
        for log_path, node in iter_timing_event_logs(run_dir, role):
            if not node:
                continue
            with log_path.open("r", encoding="utf-8", errors="replace") as handle:
                for line_no, line in enumerate(handle, start=1):
                    match = C1_TIMING_EVENT_RE.search(line)
                    if match is None:
                        continue
                    fields = parse_c1_timing_fields(match.group("fields"))
                    if fields.get("event_code") != event_code:
                        continue
                    activation_id = fields.get("activation_id", "")
                    if activation_id not in activation_ids:
                        continue
                    if not fields.get("unix_ns"):
                        continue
                    instance_key = (activation_id, event_code)
                    event_instance_counts[instance_key] = event_instance_counts.get(instance_key, 0) + 1
                    rows.append(
                        {
                            "activation_id": activation_id,
                            "transaction_id": fields.get("transaction_id", ""),
                            "delivery_path": fields.get("delivery_path", ""),
                            "event_instance_index": str(event_instance_counts[instance_key]),
                            "node": node,
                            "process": fields.get("process", "openwhisk_scheduler"),
                            "pid": fields.get("pid", ""),
                            "tid": fields.get("tid", ""),
                            "unix_ns": fields.get("unix_ns", ""),
                            "mono_ns": fields.get("mono_ns", ""),
                            "clock_domain": fields.get("clock_domain", "openwhisk_scheduler_jvm_mono"),
                            "source_log": log_path.relative_to(run_dir).as_posix(),
                            "line": str(line_no),
                        }
                    )
        if rows:
            break
    if rows:
        write_tsv(
            dst_run_dir / "extracted" / output_name,
            SCHEDULER_DISPATCH_FIELDS,
            rows,
        )
    return len(rows)


def extract_native_worker_boundaries(run_dir: Path, dst_run_dir: Path) -> int:
    return extract_invoker_timing_boundaries(
        run_dir,
        dst_run_dir,
        event_codes={"N300", "N700", "N800", "N810"},
        output_name="native-worker-boundaries.tsv",
        output_fields=NATIVE_WORKER_BOUNDARY_FIELDS,
    )


def extract_openwhisk_worker_boundaries(run_dir: Path, dst_run_dir: Path) -> int:
    return extract_invoker_timing_boundaries(
        run_dir,
        dst_run_dir,
        event_codes={"OW310", "OW500", "OW510", "OW800"},
        output_name="openwhisk-worker-boundaries.tsv",
        output_fields=OPENWHISK_WORKER_BOUNDARY_FIELDS,
    )


def invoker_from_inner_log(inner_log: str) -> str:
    name = Path(inner_log).name
    match = re.search(r"(invoker\d+)", name)
    return match.group(1) if match else ""


def extract_internal_reschedule_injections(run_dir: Path, dst_run_dir: Path) -> int:
    attempts_path = run_dir / "attempts.tsv"
    if not attempts_path.exists():
        return 0
    activation_ids = {
        row.get("activation_id", "")
        for row in read_tsv(attempts_path)
        if row.get("activation_id")
    }
    if not activation_ids:
        return 0

    rows: list[dict[str, str]] = []
    for log_path in sorted((run_dir / "nodes").glob("*/invoker.log")):
        node = log_path.parent.name
        current_inner_log = ""
        with log_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, raw_line in enumerate(handle, start=1):
                line = raw_line.rstrip("\n")
                stripped = line.strip()
                if stripped.startswith("/logs/") and "C1_INTERNAL_RESCHEDULE_INJECTION|" not in stripped:
                    current_inner_log = stripped
                    continue
                match = INTERNAL_RESCHEDULE_INJECTION_RE.search(line)
                if match is None:
                    continue
                fields = parse_c1_timing_fields(match.group("fields"))
                activation_id = fields.get("activation_id", "")
                if activation_id not in activation_ids:
                    continue
                inner_log = match.group("inner_log") or current_inner_log
                timestamp = match.group("timestamp")
                rows.append(
                    {
                        "activation_id": activation_id,
                        "node": node,
                        "invoker": invoker_from_inner_log(inner_log),
                        "timestamp": timestamp,
                        "timestamp_unix_ns": iso_timestamp_to_unix_ns(timestamp),
                        "container_id": fields.get("container_id", ""),
                        "reason": fields.get("reason", ""),
                        "status": fields.get("status", ""),
                        "source_log": log_path.relative_to(run_dir).as_posix(),
                        "line": str(line_no),
                        "inner_log": inner_log,
                        "raw_line": line,
                    }
                )
    if rows:
        write_tsv(
            dst_run_dir / "extracted" / "internal-reschedule-injections.tsv",
            INTERNAL_RESCHEDULE_INJECTION_FIELDS,
            rows,
        )
    return len(rows)


def extract_invoker_timing_boundaries(
    run_dir: Path,
    dst_run_dir: Path,
    *,
    event_codes: set[str],
    output_name: str,
    output_fields: list[str],
) -> int:
    attempts_path = run_dir / "attempts.tsv"
    if not attempts_path.exists():
        return 0
    activation_ids = {
        row.get("activation_id", "")
        for row in read_tsv(attempts_path)
        if row.get("activation_id")
    }
    if not activation_ids:
        return 0

    rows: list[dict[str, str]] = []
    event_instance_counts: dict[tuple[str, str], int] = {}
    for log_path, node in iter_timing_event_logs(run_dir, "invoker"):
        if not node:
            continue
        with log_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                match = C1_TIMING_EVENT_RE.search(line)
                if match is None:
                    continue
                fields = parse_c1_timing_fields(match.group("fields"))
                event_code = fields.get("event_code", "")
                if event_code not in event_codes:
                    continue
                activation_id = fields.get("activation_id", "")
                key = (activation_id, event_code)
                if activation_id not in activation_ids:
                    continue
                if not fields.get("unix_ns") and not fields.get("mono_ns"):
                    continue
                event_instance_counts[key] = event_instance_counts.get(key, 0) + 1
                rows.append(
                    {
                        "activation_id": activation_id,
                        "event_code": event_code,
                        "boundary_name": fields.get("boundary_name", ""),
                        "event_instance_index": str(event_instance_counts[key]),
                        "node": node,
                        "process": fields.get("process", "openwhisk_invoker"),
                        "pid": fields.get("pid", ""),
                        "tid": fields.get("tid", ""),
                        "unix_ns": fields.get("unix_ns", ""),
                        "mono_ns": fields.get("mono_ns", ""),
                        "clock_domain": fields.get("clock_domain", "openwhisk_invoker_jvm_mono"),
                        "source_log": log_path.relative_to(run_dir).as_posix(),
                        "line": str(line_no),
                        "container_id": fields.get("container_id", ""),
                        "target_container_id": fields.get("target_container_id", ""),
                        "reschedule_reason": fields.get("reschedule_reason", ""),
                        "retry_index": fields.get("retry_index", ""),
                    }
                )
    if rows:
        write_tsv(
            dst_run_dir / "extracted" / output_name,
            output_fields,
            rows,
        )
    return len(rows)


def export_round(round_root: Path, output_root: Path) -> None:
    data_root = round_root / "data"
    notes_root = round_root / "notes"
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    notes_root.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, str]] = []
    extraction_rows: list[dict[str, str]] = []
    top_level_diagnostic_counts = copy_top_level_diagnostics(data_root, output_root, manifest)
    for run_dir in iter_run_dirs(data_root):
        relative_run_dir = run_dir.relative_to(data_root)
        dst_run_dir = output_root / relative_run_dir
        for filename in sorted(SELECTED_RUN_FILES):
            src = run_dir / filename
            if src.exists() and src.is_file():
                copy_file(src, dst_run_dir / filename, manifest, output_root)
        copied_clock_sync = copy_clock_sync(run_dir, dst_run_dir, manifest, output_root)
        copied_extracted = copy_existing_extracted(run_dir, dst_run_dir)
        db_count = extract_activation_db_save(run_dir, dst_run_dir)
        nginx_count = extract_nginx_frontdoor(run_dir, dst_run_dir)
        executor_count = extract_reusable_executor(run_dir, dst_run_dir)
        controller_event_count = extract_openwhisk_controller_events(run_dir, dst_run_dir)
        scheduler_queue_enter_count = extract_openwhisk_activation_queue_enter(run_dir, dst_run_dir)
        scheduler_dispatch_count = extract_openwhisk_scheduler_dispatch(run_dir, dst_run_dir)
        native_worker_boundary_count = extract_native_worker_boundaries(run_dir, dst_run_dir)
        openwhisk_worker_boundary_count = extract_openwhisk_worker_boundaries(run_dir, dst_run_dir)
        internal_reschedule_injection_count = extract_internal_reschedule_injections(run_dir, dst_run_dir)
        final_extracted_counts = {
            extracted.name: count_tsv_rows(extracted)
            for extracted in sorted((dst_run_dir / "extracted").glob("*.tsv"))
        }
        for extracted in sorted((dst_run_dir / "extracted").glob("*.tsv")):
            manifest.append(
                {
                    "relative_path": extracted.relative_to(output_root).as_posix(),
                    "bytes": str(extracted.stat().st_size),
                    "sha256": sha256_file(extracted),
                }
            )
        extraction_rows.append(
            {
                "run_dir": relative_run_dir.as_posix(),
                "activation_db_save_rows": str(db_count),
                "nginx_frontdoor_rows": str(nginx_count),
                "reusable_executor_rows": str(executor_count),
                "openwhisk_controller_event_rows": str(controller_event_count),
                "openwhisk_activation_queue_enter_rows": str(scheduler_queue_enter_count),
                "openwhisk_scheduler_dispatch_rows": str(scheduler_dispatch_count),
                "native_worker_boundary_rows": str(native_worker_boundary_count),
                "openwhisk_worker_boundary_rows": str(openwhisk_worker_boundary_count),
                "internal_reschedule_injection_rows": str(internal_reschedule_injection_count),
                "copied_extracted_files": ",".join(sorted(copied_extracted)),
                "copied_clock_sync_files": ",".join(copied_clock_sync),
                "final_extracted_rows": ",".join(
                    f"{name}:{count}" for name, count in sorted(final_extracted_counts.items())
                ),
            }
        )

    write_tsv(output_root / "EXPORT-MANIFEST.tsv", ["relative_path", "bytes", "sha256"], manifest)
    write_tsv(
        notes_root / "light-data-export-summary.tsv",
        [
            "run_dir",
            "activation_db_save_rows",
            "nginx_frontdoor_rows",
            "reusable_executor_rows",
            "openwhisk_controller_event_rows",
            "openwhisk_activation_queue_enter_rows",
            "openwhisk_scheduler_dispatch_rows",
            "native_worker_boundary_rows",
            "openwhisk_worker_boundary_rows",
            "internal_reschedule_injection_rows",
            "copied_extracted_files",
            "copied_clock_sync_files",
            "final_extracted_rows",
        ],
        extraction_rows,
    )
    write_tsv(
        notes_root / "light-data-export-diagnostics.tsv",
        ["data_dir", "file_count"],
        [
            {"data_dir": name, "file_count": str(count)}
            for name, count in sorted(top_level_diagnostic_counts.items())
        ],
    )
    (notes_root / "raw-data-remote.env").write_text(
        "\n".join(
            [
                "local_data_mode=light",
                "local_data_semantics=lossless_structured_no_raw_log_noise",
                f"raw_data_remote={data_root}",
                f"light_data_remote={output_root}",
                "retained_structured_artifacts=per-run config, per-request logical TSV, per-attempt TSV, placements, retry stats, premeasure/warmup tables, clock-sync TSVs, and extracted per-marker TSVs",
                "retained_timing_artifacts=timing-events.tsv, entity-map.tsv, event-attrs.tsv, phase-durations.tsv, phase-summary.tsv, phase-coverage.tsv, boundary-quality.tsv when materialized",
                "timing_event_source_policy=prefer structured-timing-events/*.c1timing.log; legacy nodes/*/*.log is fallback compatibility and must be bounded current-run event evidence in filtered mode",
                "retained_premeasurement_diagnostics=profile-logs and marker-runtime-probe directories when present",
                "omitted_raw_artifacts=bulk node logs and other non-structured raw files",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    export_round(args.round_root, args.output)


if __name__ == "__main__":
    main()
