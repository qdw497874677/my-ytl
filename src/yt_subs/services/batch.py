"""Playlist-scale subtitle batch orchestration service."""

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from yt_subs.domain.models import (
    BatchItemRecord,
    BatchJobManifest,
    BatchRunLogEvent,
    BatchRunSummary,
    FailureRecord,
    InspectItem,
    JobOptions,
    MissingSubtitle,
    OutputIdentity,
    SubtitleDownloadOptions,
    SubtitleDownloadResult,
    SubtitleFormat,
    SubtitleTrack,
)
from yt_subs.services.inspect import Inspector, inspect_target
from yt_subs.services.job_manifest import append_run_log, write_manifest, write_run_summary
from yt_subs.services.subtitles import download_subtitles

ProgressCallback = Callable[[BatchRunLogEvent], None]
DownloadCallable = Callable[[InspectItem, SubtitleDownloadOptions], SubtitleDownloadResult]


class BatchSubtitleOptions(BaseModel):
    """User-facing options for playlist-scale subtitle batch jobs."""

    model_config = ConfigDict(frozen=True)

    output_dir: Path = Path("downloads")
    languages: list[str] = Field(default_factory=lambda: ["en"])
    formats: list[SubtitleFormat] = Field(default_factory=lambda: ["vtt"])
    include_automatic: bool = True


def run_batch_subtitle_job(
    url: str,
    options: BatchSubtitleOptions | SubtitleDownloadOptions,
    *,
    inspector: Inspector | None = None,
    downloader_factory: DownloadCallable | None = None,
    progress_callback: ProgressCallback | None = None,
) -> BatchRunSummary:
    """Run a resilient subtitle batch job over all inspected target items."""

    batch_options = _coerce_batch_options(options)
    job_id = f"batch-{uuid4().hex}"
    job_dir = batch_options.output_dir / "batch-jobs" / job_id
    manifest = BatchJobManifest(
        job_id=job_id,
        created_at=_utc_now(),
        source_url=url,
        output_dir=batch_options.output_dir,
        requested_languages=list(batch_options.languages),
        requested_formats=list(batch_options.formats),
        include_automatic=batch_options.include_automatic,
        manifest_path=job_dir / "manifest.json",
        log_path=job_dir / "run.jsonl",
        summary_path=job_dir / "summary.json",
        items=[],
    )

    report = inspect_target(
        url,
        JobOptions(
            output_dir=batch_options.output_dir,
            languages=list(batch_options.languages),
            include_automatic=batch_options.include_automatic,
        ),
        inspector=inspector,
    )
    manifest = manifest.model_copy(
        update={
            "items": [
                BatchItemRecord(item=planned.item, identity=planned.identity)
                for planned in report.items
            ]
        }
    )
    write_manifest(manifest)
    _log(manifest, "job_started", "Batch subtitle job started", progress_callback=progress_callback)

    records = list(manifest.items)
    for index, record in enumerate(records):
        record = record.model_copy(update={"status": "running", "started_at": _utc_now()})
        records[index] = record
        manifest = manifest.model_copy(update={"items": records})
        write_manifest(manifest)
        _log(
            manifest,
            "item_started",
            f"Started {record.item.video_id}",
            item=record.item,
            progress_callback=progress_callback,
        )

        record = execute_batch_item(record, batch_options, downloader_factory)
        records[index] = record
        manifest = manifest.model_copy(update={"items": records})
        write_manifest(manifest)
        event_name = _event_for_status(record.status)
        _log(
            manifest,
            event_name,
            f"{record.item.video_id} {record.status}",
            item=record.item,
            level="error" if record.status.startswith("failed") else "info",
            details={"status": record.status, "attempts": record.attempts},
            progress_callback=progress_callback,
        )

    summary = write_run_summary(manifest)
    _log(manifest, "job_completed", "Batch subtitle job completed", progress_callback=progress_callback)
    return summary


def should_skip_completed_item(
    record: BatchItemRecord, options: BatchSubtitleOptions | SubtitleDownloadOptions
) -> bool:
    """Conservatively skip only when metadata and all requested artifacts already exist."""

    batch_options = _coerce_batch_options(options)
    if not record.identity.metadata_path.exists():
        return False
    required_paths = _required_artifact_paths(record.item, record.identity, batch_options)
    return bool(required_paths) and all(path.exists() for path in required_paths)


def classify_failure(exc: Exception) -> FailureRecord:
    """Classify exceptions into retryable or permanent batch failures."""

    if isinstance(exc, NoSubtitlesError):
        return FailureRecord(
            category="permanent",
            code="unavailable_subtitles",
            message=str(exc),
        )
    if isinstance(exc, PermanentBatchError):
        return FailureRecord(category="permanent", code=exc.code, message=str(exc))
    return FailureRecord(
        category="retryable",
        code=exc.__class__.__name__,
        message=str(exc) or "retryable batch item failure",
    )


class PermanentBatchError(Exception):
    """Permanent item failure that should not be retried."""

    def __init__(self, message: str, *, code: str = "permanent_failure") -> None:
        super().__init__(message)
        self.code = code


class NoSubtitlesError(PermanentBatchError):
    """Requested subtitles are unavailable for this item."""

    def __init__(self, message: str = "requested subtitles unavailable") -> None:
        super().__init__(message, code="unavailable_subtitles")


class _SingleItemInspector:
    def __init__(self, item: InspectItem) -> None:
        self._item = item

    def inspect(self, url: str) -> list[InspectItem]:
        return [self._item]


def execute_batch_item(
    record: BatchItemRecord,
    options: BatchSubtitleOptions,
    downloader_factory: DownloadCallable | None,
) -> BatchItemRecord:
    attempts = record.attempts
    try:
        if should_skip_completed_item(record, options):
            return record.model_copy(
                update={"status": "skipped", "attempts": attempts, "completed_at": _utc_now()}
            )

        if not _available_requested_tracks(record.item.subtitles, options):
            raise NoSubtitlesError()

        attempts += 1
        download_options = SubtitleDownloadOptions(
            output_dir=options.output_dir,
            languages=list(options.languages),
            formats=list(options.formats),
            include_automatic=options.include_automatic,
        )
        result = (
            downloader_factory(record.item, download_options)
            if downloader_factory is not None
            else download_subtitles(
                str(record.item.webpage_url),
                download_options,
                inspector=_SingleItemInspector(record.item),
            )
        )
        if not result.artifacts and result.missing_subtitles:
            raise NoSubtitlesError()
        return record.model_copy(
            update={
                "status": "completed",
                "artifacts": list(result.artifacts),
                "missing_subtitles": list(result.missing_subtitles),
                "attempts": attempts,
                "completed_at": _utc_now(),
                "error": None,
            }
        )
    except Exception as exc:
        failure = classify_failure(exc)
        status = "failed_retryable" if failure.category == "retryable" else "failed_permanent"
        if failure.code == "unavailable_subtitles":
            status = "no_subtitles"
        return record.model_copy(
            update={
                "status": status,
                "attempts": attempts,
                "completed_at": _utc_now(),
                "error": failure,
            }
        )


def _required_artifact_paths(
    item: InspectItem, identity: OutputIdentity, options: BatchSubtitleOptions
) -> list[Path]:
    paths: list[Path] = []
    for track in _available_requested_tracks(item.subtitles, options):
        for fmt in options.formats:
            paths.append(identity.subtitles_dir / f"{track.language_code}.{track.kind}.{fmt}")
    return paths


def _available_requested_tracks(
    tracks: list[SubtitleTrack], options: BatchSubtitleOptions
) -> list[SubtitleTrack]:
    by_lang: dict[str, SubtitleTrack] = {}
    requested = set(options.languages)
    for track in tracks:
        if track.language_code not in requested:
            continue
        if track.kind == "automatic" and not options.include_automatic:
            continue
        existing = by_lang.get(track.language_code)
        if existing is None or (track.kind == "manual" and existing.kind == "automatic"):
            by_lang[track.language_code] = track
    return list(by_lang.values())


def _coerce_batch_options(
    options: BatchSubtitleOptions | SubtitleDownloadOptions,
) -> BatchSubtitleOptions:
    if isinstance(options, BatchSubtitleOptions):
        return options
    return BatchSubtitleOptions(
        output_dir=options.output_dir,
        languages=list(options.languages),
        formats=list(options.formats),
        include_automatic=options.include_automatic,
    )


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
    item: InspectItem | None = None,
    level: str = "info",
    details: dict[str, object] | None = None,
    progress_callback: ProgressCallback | None = None,
) -> BatchRunLogEvent:
    log_event = append_run_log(
        manifest,
        event,
        message,
        item_video_id=item.video_id if item else None,
        level=level,  # type: ignore[arg-type]
        details=details,
    )
    if progress_callback is not None:
        progress_callback(log_event)
    return log_event


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
