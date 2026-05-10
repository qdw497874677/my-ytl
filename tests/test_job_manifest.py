"""Tests for batch manifest contracts and persistence helpers."""

import json
from pathlib import Path

from yt_subs.domain.models import (
    BatchItemRecord,
    BatchJobManifest,
    FailureRecord,
    InspectItem,
    MissingSubtitle,
    OutputIdentity,
    SubtitleArtifact,
    SubtitleProvenance,
)
from yt_subs.services.job_manifest import (
    append_run_log,
    read_manifest,
    write_manifest,
    write_run_summary,
)


YOUTUBE_URL = "https://www.youtube.com/watch?v=abc123"


def _identity(tmp_path: Path, video_id: str = "abc123") -> OutputIdentity:
    bundle_dir = tmp_path / "items" / video_id
    return OutputIdentity(
        video_id=video_id,
        item_key=video_id,
        title="Example",
        bundle_dir=bundle_dir,
        metadata_path=bundle_dir / "metadata" / "item.json",
        subtitles_dir=bundle_dir / "subtitles",
        logs_dir=bundle_dir / "logs",
        media_dir=bundle_dir / "media",
    )


def _item(video_id: str = "abc123") -> InspectItem:
    return InspectItem(
        video_id=video_id,
        title="Example",
        webpage_url=f"https://www.youtube.com/watch?v={video_id}",
    )


def _artifact(tmp_path: Path, video_id: str = "abc123") -> SubtitleArtifact:
    identity = _identity(tmp_path, video_id)
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
    return BatchJobManifest(
        job_id="job-123",
        created_at="2026-05-10T00:00:00Z",
        source_url=YOUTUBE_URL,
        output_dir=tmp_path,
        requested_languages=["en", "ja"],
        requested_formats=["vtt", "srt"],
        include_automatic=True,
        manifest_path=tmp_path / "job-123" / "manifest.json",
        log_path=tmp_path / "job-123" / "run.jsonl",
        summary_path=tmp_path / "job-123" / "summary.json",
        items=[
            BatchItemRecord(
                item=_item("done1"),
                identity=_identity(tmp_path, "done1"),
                status="completed",
                artifacts=[_artifact(tmp_path, "done1")],
                attempts=1,
                started_at="2026-05-10T00:00:01Z",
                completed_at="2026-05-10T00:00:02Z",
            ),
            BatchItemRecord(
                item=_item("retry1"),
                identity=_identity(tmp_path, "retry1"),
                status="failed_retryable",
                error=FailureRecord(
                    category="retryable",
                    code="network_error",
                    message="temporary network error",
                    detail="timeout",
                ),
                attempts=1,
            ),
            BatchItemRecord(
                item=_item("perm1"),
                identity=_identity(tmp_path, "perm1"),
                status="failed_permanent",
                error=FailureRecord(
                    category="permanent",
                    code="unsupported_content",
                    message="unsupported content",
                ),
                attempts=1,
            ),
            BatchItemRecord(
                item=_item("nosub1"),
                identity=_identity(tmp_path, "nosub1"),
                status="no_subtitles",
                missing_subtitles=[MissingSubtitle(language_code="ja", reason="unavailable")],
                error=FailureRecord(
                    category="permanent",
                    code="unavailable_subtitles",
                    message="requested subtitles unavailable",
                ),
                attempts=1,
            ),
        ],
    )


def test_batch_manifest_contracts_are_json_safe(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)

    dumped = manifest.model_dump(mode="json")
    encoded = json.dumps(dumped, ensure_ascii=False)
    loaded = BatchJobManifest.model_validate_json(encoded)

    assert dumped["manifest_path"].endswith("manifest.json")
    assert loaded.job_id == "job-123"
    assert [item.status for item in loaded.items] == [
        "completed",
        "failed_retryable",
        "failed_permanent",
        "no_subtitles",
    ]
    assert loaded.items[1].error is not None
    assert loaded.items[1].error.category == "retryable"
    assert loaded.items[2].error is not None
    assert loaded.items[2].error.category == "permanent"


def test_manifest_log_and_summary_persistence_round_trip(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)

    write_manifest(manifest)
    loaded = read_manifest(manifest.manifest_path)
    event = append_run_log(
        loaded,
        "item_failed",
        "retryable item failed",
        item_video_id="retry1",
        level="warning",
        details={"status": "failed_retryable"},
        timestamp="2026-05-10T00:00:03Z",
    )
    summary = write_run_summary(loaded)

    manifest_json = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))
    log_lines = manifest.log_path.read_text(encoding="utf-8").splitlines()
    log_json = json.loads(log_lines[0])
    summary_json = json.loads(manifest.summary_path.read_text(encoding="utf-8"))

    assert manifest_json["job_id"] == "job-123"
    assert event.event == "item_failed"
    assert log_json == {
        "details": {"status": "failed_retryable"},
        "event": "item_failed",
        "item_video_id": "retry1",
        "level": "warning",
        "message": "retryable item failed",
        "timestamp": "2026-05-10T00:00:03Z",
    }
    assert summary.total == 4
    assert summary_json["completed"] == 1
    assert summary_json["failed_retryable"] == 1
    assert summary_json["failed_permanent"] == 1
    assert summary_json["no_subtitles"] == 1
