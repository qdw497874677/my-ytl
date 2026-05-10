"""Manifest-driven rerun service for retryable batch item failures."""

from collections.abc import Callable
from pathlib import Path

from yt_subs.domain.models import BatchJobManifest, BatchRunLogEvent, BatchRunSummary
from yt_subs.services.batch import BatchSubtitleOptions, DownloadCallable, execute_batch_item
from yt_subs.services.job_manifest import append_run_log, read_manifest, write_manifest, write_run_summary

ProgressCallback = Callable[[BatchRunLogEvent], None]


def rerun_failed_items(
    manifest_path: str | Path,
    *,
    downloader_factory: DownloadCallable | None = None,
    progress_callback: ProgressCallback | None = None,
) -> BatchRunSummary:
    """Rerun only retryable failures from a persisted batch manifest."""

    manifest = read_manifest(manifest_path)
    options = BatchSubtitleOptions(
        output_dir=manifest.output_dir,
        languages=list(manifest.requested_languages),
        formats=list(manifest.requested_formats),
        include_automatic=manifest.include_automatic,
    )
    retryable_indexes = [
        index for index, record in enumerate(manifest.items) if record.status == "failed_retryable"
    ]

    _log(
        manifest,
        "rerun_started",
        "Failed-item rerun started",
        details={"source_manifest": str(manifest_path), "attempted": len(retryable_indexes)},
        progress_callback=progress_callback,
    )

    if not retryable_indexes:
        summary = write_run_summary(manifest)
        _log(
            manifest,
            "rerun_completed",
            "Failed-item rerun completed with no retryable items",
            details={"source_manifest": str(manifest_path), "attempted": 0},
            progress_callback=progress_callback,
        )
        return summary

    records = list(manifest.items)
    for index in retryable_indexes:
        record = records[index]
        _log(
            manifest,
            "item_started",
            f"Rerun started {record.item.video_id}",
            item_video_id=record.item.video_id,
            progress_callback=progress_callback,
        )
        updated = execute_batch_item(record, options, downloader_factory)
        records[index] = updated
        manifest = manifest.model_copy(update={"items": records})
        write_manifest(manifest)
        _log(
            manifest,
            _event_for_status(updated.status),
            f"Rerun {updated.item.video_id} {updated.status}",
            item_video_id=updated.item.video_id,
            level="error" if updated.status.startswith("failed") else "info",
            details={"status": updated.status, "attempts": updated.attempts},
            progress_callback=progress_callback,
        )

    summary = write_run_summary(manifest)
    _log(
        manifest,
        "rerun_completed",
        "Failed-item rerun completed",
        details={"source_manifest": str(manifest_path), "attempted": len(retryable_indexes)},
        progress_callback=progress_callback,
    )
    return summary


def _event_for_status(status: str) -> str:
    return {
        "completed": "item_completed",
        "skipped": "item_skipped",
        "failed_retryable": "item_failed",
        "failed_permanent": "item_failed",
        "no_subtitles": "item_failed",
    }.get(status, "item_updated")


def _log(
    manifest: BatchJobManifest,
    event: str,
    message: str,
    *,
    item_video_id: str | None = None,
    level: str = "info",
    details: dict[str, object] | None = None,
    progress_callback: ProgressCallback | None = None,
) -> BatchRunLogEvent:
    log_event = append_run_log(
        manifest,
        event,
        message,
        item_video_id=item_video_id,
        level=level,  # type: ignore[arg-type]
        details=details,
    )
    if progress_callback is not None:
        progress_callback(log_event)
    return log_event
