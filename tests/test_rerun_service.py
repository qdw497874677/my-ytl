"""Tests for manifest-driven failed item reruns."""

from pathlib import Path

from yt_subs.domain.models import (
    BatchItemRecord,
    BatchJobManifest,
    FailureRecord,
    InspectItem,
    MissingSubtitle,
    OutputIdentity,
    SubtitleArtifact,
    SubtitleDownloadResult,
    SubtitleProvenance,
    SubtitleTrack,
)
from yt_subs.services.job_manifest import read_manifest, write_manifest
from yt_subs.services.rerun import rerun_failed_items

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PL123"


def _item(video_id: str) -> InspectItem:
    return InspectItem(
        video_id=video_id,
        title=f"Video {video_id}",
        webpage_url=f"https://www.youtube.com/watch?v={video_id}",
        subtitles=[SubtitleTrack(language_code="en", kind="manual", source_format="vtt")],
    )


def _identity(tmp_path: Path, video_id: str) -> OutputIdentity:
    bundle_dir = tmp_path / "items" / video_id
    return OutputIdentity(
        video_id=video_id,
        item_key=video_id,
        title=f"Video {video_id}",
        bundle_dir=bundle_dir,
        metadata_path=bundle_dir / "metadata" / "item.json",
        subtitles_dir=bundle_dir / "subtitles",
        logs_dir=bundle_dir / "logs",
        media_dir=bundle_dir / "media",
    )


def _artifact(identity: OutputIdentity) -> SubtitleArtifact:
    return SubtitleArtifact(
        language_code="en",
        kind="manual",
        format="vtt",
        path=identity.subtitles_dir / "en.manual.vtt",
        provenance=SubtitleProvenance(
            source_path=identity.subtitles_dir / "source.en.vtt",
            source_format="vtt",
            source_language_code="en",
            source_kind="manual",
        ),
    )


def _manifest(tmp_path: Path) -> BatchJobManifest:
    records = [
        BatchItemRecord(
            item=_item("done"),
            identity=_identity(tmp_path, "done"),
            status="completed",
            attempts=1,
        ),
        BatchItemRecord(
            item=_item("skipped"),
            identity=_identity(tmp_path, "skipped"),
            status="skipped",
            attempts=1,
        ),
        BatchItemRecord(
            item=_item("retry"),
            identity=_identity(tmp_path, "retry"),
            status="failed_retryable",
            attempts=1,
            error=FailureRecord(category="retryable", code="TimeoutError", message="timeout"),
        ),
        BatchItemRecord(
            item=_item("perm"),
            identity=_identity(tmp_path, "perm"),
            status="failed_permanent",
            attempts=1,
            error=FailureRecord(category="permanent", code="unsupported", message="unsupported"),
        ),
        BatchItemRecord(
            item=_item("nosub"),
            identity=_identity(tmp_path, "nosub"),
            status="no_subtitles",
            attempts=1,
            missing_subtitles=[MissingSubtitle(language_code="en", reason="unavailable")],
            error=FailureRecord(
                category="permanent", code="unavailable_subtitles", message="no subtitles"
            ),
        ),
    ]
    return BatchJobManifest(
        job_id="job-123",
        created_at="2026-05-10T00:00:00Z",
        source_url=PLAYLIST_URL,
        output_dir=tmp_path,
        requested_languages=["en"],
        requested_formats=["vtt"],
        include_automatic=True,
        manifest_path=tmp_path / "batch-jobs" / "job-123" / "manifest.json",
        log_path=tmp_path / "batch-jobs" / "job-123" / "run.jsonl",
        summary_path=tmp_path / "batch-jobs" / "job-123" / "summary.json",
        items=records,
    )


def _result(item: InspectItem, tmp_path: Path) -> SubtitleDownloadResult:
    identity = _identity(tmp_path, item.video_id)
    artifact = _artifact(identity)
    artifact.path.parent.mkdir(parents=True, exist_ok=True)
    artifact.path.write_text("WEBVTT\n", encoding="utf-8")
    identity.metadata_path.parent.mkdir(parents=True, exist_ok=True)
    identity.metadata_path.write_text("{}", encoding="utf-8")
    return SubtitleDownloadResult(
        item=item,
        identity=identity,
        artifacts=[artifact],
        missing_subtitles=[],
        metadata_path=identity.metadata_path,
    )


def test_rerun_selects_only_retryable_failures(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    write_manifest(manifest)
    attempted: list[str] = []

    def fake_download(item: InspectItem, options):
        attempted.append(item.video_id)
        return _result(item, tmp_path)

    summary = rerun_failed_items(manifest.manifest_path, downloader_factory=fake_download)
    updated = read_manifest(summary.manifest_path)

    assert attempted == ["retry"]
    assert [record.status for record in updated.items] == [
        "completed",
        "skipped",
        "completed",
        "failed_permanent",
        "no_subtitles",
    ]
    assert updated.items[2].attempts == 2
    assert summary.completed == 2
    assert summary.failed_permanent == 1
    assert summary.no_subtitles == 1


def test_rerun_skips_already_completed_artifacts_and_preserves_permanent(
    tmp_path: Path,
) -> None:
    manifest = _manifest(tmp_path)
    retry_identity = manifest.items[2].identity
    retry_identity.metadata_path.parent.mkdir(parents=True, exist_ok=True)
    retry_identity.subtitles_dir.mkdir(parents=True, exist_ok=True)
    retry_identity.metadata_path.write_text("{}", encoding="utf-8")
    (retry_identity.subtitles_dir / "en.manual.vtt").write_text("WEBVTT\n", encoding="utf-8")
    write_manifest(manifest)

    attempted: list[str] = []
    events: list[str] = []
    summary = rerun_failed_items(
        manifest.manifest_path,
        downloader_factory=lambda item, options: attempted.append(item.video_id),
        progress_callback=lambda event: events.append(event.event),
    )
    updated = read_manifest(summary.manifest_path)

    assert attempted == []
    assert updated.items[2].status == "skipped"
    assert updated.items[2].attempts == 1
    assert updated.items[3].status == "failed_permanent"
    assert updated.items[4].status == "no_subtitles"
    assert summary.skipped == 2
    assert "rerun_started" in events
    assert "item_skipped" in events
    assert "rerun_completed" in events
