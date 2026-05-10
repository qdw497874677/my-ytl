"""Tests for resilient playlist-scale batch subtitle execution."""

import json
from pathlib import Path

from yt_subs.domain.models import (
    InspectItem,
    OutputIdentity,
    SubtitleArtifact,
    SubtitleDownloadResult,
    SubtitleProvenance,
    SubtitleTrack,
)
from yt_subs.services.batch import BatchSubtitleOptions, run_batch_subtitle_job
from yt_subs.services.job_manifest import read_manifest

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PL123"


class FakeInspector:
    def __init__(self, items: list[InspectItem]) -> None:
        self.items = items

    def inspect(self, url: str) -> list[InspectItem]:
        return self.items


def _item(video_id: str, index: int, subtitles: list[SubtitleTrack] | None = None) -> InspectItem:
    return InspectItem(
        video_id=video_id,
        title=f"Video {video_id}",
        webpage_url=f"https://www.youtube.com/watch?v={video_id}",
        playlist_index=index,
        subtitles=subtitles
        if subtitles is not None
        else [SubtitleTrack(language_code="en", kind="manual", source_format="vtt")],
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


def _result(item: InspectItem, tmp_path: Path) -> SubtitleDownloadResult:
    identity = OutputIdentity(
        video_id=item.video_id,
        item_key=item.video_id,
        title=item.title,
        bundle_dir=tmp_path / "items" / item.video_id,
        metadata_path=tmp_path / "items" / item.video_id / "metadata" / "item.json",
        subtitles_dir=tmp_path / "items" / item.video_id / "subtitles",
        logs_dir=tmp_path / "items" / item.video_id / "logs",
        media_dir=tmp_path / "items" / item.video_id / "media",
    )
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


def test_batch_continues_after_retryable_item_failure(tmp_path: Path) -> None:
    items = [_item("one", 1), _item("two", 2), _item("three", 3)]
    calls: list[str] = []

    def fake_download(item: InspectItem, options):
        calls.append(item.video_id)
        if item.video_id == "two":
            raise TimeoutError("temporary timeout")
        return _result(item, tmp_path)

    summary = run_batch_subtitle_job(
        PLAYLIST_URL,
        BatchSubtitleOptions(output_dir=tmp_path, languages=["en"], formats=["vtt"]),
        inspector=FakeInspector(items),
        downloader_factory=fake_download,
    )
    manifest = read_manifest(summary.manifest_path)

    assert calls == ["one", "two", "three"]
    assert summary.total == 3
    assert summary.completed == 2
    assert summary.failed_retryable == 1
    assert [item.status for item in manifest.items] == [
        "completed",
        "failed_retryable",
        "completed",
    ]
    assert manifest.items[1].error is not None
    assert manifest.items[1].error.category == "retryable"


def test_skip_no_subtitles_progress_and_jsonl_logs(tmp_path: Path) -> None:
    completed = _item("done", 1)
    no_subtitles = _item("nosub", 2, subtitles=[])
    fresh = _item("fresh", 3)
    calls: list[str] = []
    events: list[str] = []

    # Pre-create exactly the artifact names planned by the batch skip policy.
    done_dir = tmp_path / "items" / "done-Video-done"
    (done_dir / "metadata").mkdir(parents=True)
    (done_dir / "subtitles").mkdir(parents=True)
    (done_dir / "metadata" / "item.json").write_text("{}", encoding="utf-8")
    (done_dir / "subtitles" / "en.manual.vtt").write_text("WEBVTT\n", encoding="utf-8")

    def fake_download(item: InspectItem, options):
        calls.append(item.video_id)
        return _result(item, tmp_path)

    summary = run_batch_subtitle_job(
        PLAYLIST_URL,
        BatchSubtitleOptions(output_dir=tmp_path, languages=["en"], formats=["vtt"]),
        inspector=FakeInspector([completed, no_subtitles, fresh]),
        downloader_factory=fake_download,
        progress_callback=lambda event: events.append(event.event),
    )
    manifest = read_manifest(summary.manifest_path)
    log_events = [json.loads(line)["event"] for line in summary.log_path.read_text(
        encoding="utf-8"
    ).splitlines()]

    assert calls == ["fresh"]
    assert summary.skipped == 1
    assert summary.no_subtitles == 1
    assert summary.completed == 1
    assert [item.status for item in manifest.items] == ["skipped", "no_subtitles", "completed"]
    assert "item_started" in events
    assert "item_completed" in events
    assert "item_skipped" in events
    assert "item_failed" in events
    assert "job_completed" in events
    assert log_events == events


def test_batch_propagates_network_stability_options_to_single_item_downloads(
    tmp_path: Path,
) -> None:
    items = [_item("one", 1)]
    captured = {}

    def fake_download(item: InspectItem, options):
        captured["force_ipv4"] = options.force_ipv4
        captured["retries"] = options.retries
        captured["extractor_retries"] = options.extractor_retries
        return _result(item, tmp_path)

    summary = run_batch_subtitle_job(
        PLAYLIST_URL,
        BatchSubtitleOptions(
            output_dir=tmp_path,
            languages=["en"],
            formats=["vtt"],
            force_ipv4=False,
            retries=7,
            extractor_retries=9,
        ),
        inspector=FakeInspector(items),
        downloader_factory=fake_download,
    )

    assert summary.completed == 1
    assert captured == {"force_ipv4": False, "retries": 7, "extractor_retries": 9}
