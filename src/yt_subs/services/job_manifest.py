"""Filesystem persistence helpers for batch manifests, logs, and summaries."""

import json
from datetime import UTC, datetime
from pathlib import Path

from yt_subs.domain.models import BatchJobManifest, BatchRunLogEvent, BatchRunSummary, LogLevel


def write_manifest(manifest: BatchJobManifest) -> BatchJobManifest:
    """Persist a batch manifest as deterministic pretty JSON."""

    manifest.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return manifest


def read_manifest(path: str | Path) -> BatchJobManifest:
    """Load a saved batch manifest into the domain contract."""

    return BatchJobManifest.model_validate_json(Path(path).read_text(encoding="utf-8"))


def append_run_log(
    manifest: BatchJobManifest,
    event: str,
    message: str,
    *,
    item_video_id: str | None = None,
    level: LogLevel = "info",
    details: dict[str, object] | None = None,
    timestamp: str | None = None,
) -> BatchRunLogEvent:
    """Append one JSON object per line to the manifest's durable run log."""

    log_event = BatchRunLogEvent(
        event=event,
        timestamp=timestamp or _utc_now(),
        level=level,
        message=message,
        item_video_id=item_video_id,
        details=details or {},
    )
    manifest.log_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest.log_path.open("a", encoding="utf-8") as handle:
        line = json.dumps(log_event.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
        handle.write(line)
        handle.write("\n")
    return log_event


def write_run_summary(manifest: BatchJobManifest) -> BatchRunSummary:
    """Compute and persist a stable machine-readable summary for a manifest."""

    counts = {
        "completed": 0,
        "skipped": 0,
        "failed_retryable": 0,
        "failed_permanent": 0,
        "no_subtitles": 0,
    }
    for item in manifest.items:
        if item.status in counts:
            counts[item.status] += 1

    summary = BatchRunSummary(
        job_id=manifest.job_id,
        source_url=manifest.source_url,
        total=len(manifest.items),
        completed=counts["completed"],
        skipped=counts["skipped"],
        failed_retryable=counts["failed_retryable"],
        failed_permanent=counts["failed_permanent"],
        no_subtitles=counts["no_subtitles"],
        manifest_path=manifest.manifest_path,
        log_path=manifest.log_path,
        summary_path=manifest.summary_path,
    )
    manifest.summary_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.summary_path.write_text(
        json.dumps(summary.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return summary


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
