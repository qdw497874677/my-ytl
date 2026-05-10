"""Tests for batch and rerun CLI commands."""

import json
from pathlib import Path

from typer.testing import CliRunner

from yt_subs.domain.models import BatchRunLogEvent, BatchRunSummary
from yt_subs.interfaces import cli
from yt_subs.interfaces.cli import app

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PL123"


def _summary(tmp_path: Path) -> BatchRunSummary:
    return BatchRunSummary(
        job_id="job-123",
        source_url=PLAYLIST_URL,
        total=3,
        completed=1,
        skipped=1,
        failed_retryable=1,
        failed_permanent=0,
        no_subtitles=0,
        manifest_path=tmp_path / "batch-jobs" / "job-123" / "manifest.json",
        log_path=tmp_path / "batch-jobs" / "job-123" / "run.jsonl",
        summary_path=tmp_path / "batch-jobs" / "job-123" / "summary.json",
    )


def test_batch_command_passes_options_and_prints_json_summary(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    def fake_batch(url: str, options, *, progress_callback=None, **kwargs):
        captured["url"] = url
        captured["languages"] = options.languages
        captured["formats"] = options.formats
        captured["output_dir"] = options.output_dir
        captured["include_automatic"] = options.include_automatic
        captured["progress_callback"] = progress_callback
        captured["inspector"] = kwargs.get("inspector")
        return _summary(tmp_path)

    monkeypatch.setattr(cli, "run_batch_subtitle_job", fake_batch)

    result = CliRunner().invoke(
        app,
        [
            "batch",
            PLAYLIST_URL,
            "--language",
            "en",
            "--format",
            "vtt",
            "--format",
            "srt",
            "--output-dir",
            str(tmp_path),
            "--manual-only",
            "--json-summary",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["job_id"] == "job-123"
    assert payload["failed_retryable"] == 1
    assert captured == {
        "url": PLAYLIST_URL,
        "languages": ["en"],
        "formats": ["vtt", "srt"],
        "output_dir": tmp_path,
        "include_automatic": False,
        "progress_callback": None,
        "inspector": captured["inspector"],
    }


def test_rerun_command_delegates_and_prints_json_summary(monkeypatch, tmp_path: Path) -> None:
    captured = {}
    manifest_path = tmp_path / "manifest.json"

    def fake_rerun(path: Path, *, progress_callback=None, **kwargs):
        captured["path"] = path
        captured["progress_callback"] = progress_callback
        return _summary(tmp_path)

    monkeypatch.setattr(cli, "rerun_failed_items", fake_rerun)

    result = CliRunner().invoke(app, ["rerun", str(manifest_path), "--json-summary"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["manifest_path"].endswith("manifest.json")
    assert captured == {"path": manifest_path, "progress_callback": None}


def test_batch_human_output_includes_progress_and_summary(monkeypatch, tmp_path: Path) -> None:
    def fake_batch(url: str, options, *, progress_callback=None, **kwargs):
        if progress_callback is not None:
            progress_callback(
                BatchRunLogEvent(
                    event="item_completed",
                    item_video_id="abc123",
                    level="info",
                    message="abc123 completed",
                    timestamp="2026-05-10T00:00:00Z",
                    details={"status": "completed"},
                )
            )
        return _summary(tmp_path)

    monkeypatch.setattr(cli, "run_batch_subtitle_job", fake_batch)

    result = CliRunner().invoke(app, ["batch", PLAYLIST_URL, "--output-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert "item_completed" in result.output
    assert "Failed retryable" in result.output
    assert "Manifest:" in result.output


def test_batch_validation_errors_exit_two(monkeypatch, tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["batch", PLAYLIST_URL, "--format", "invalid", "--output-dir", str(tmp_path)],
    )

    assert result.exit_code == 2


def test_batch_help_mentions_auto_cookie_detection_and_zen() -> None:
    result = CliRunner().invoke(app, ["batch", "--help"])

    assert result.exit_code == 0
    assert "auto-detects" in result.output.lower()
    assert "common browsers" in result.output.lower()
    assert "firefox-compati" in result.output.lower()
    assert "--remote-compone" in result.output
    assert "--no-remote-comp" in result.output
    assert "ejs:github" in result.output
    assert "--force-ipv4" in result.output
    assert "--extractor-retries" in result.output
    assert "--retries" in result.output


def test_batch_command_passes_remote_components_to_inspector(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    class FakeInspector:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

        def inspect(self, url: str):
            return []

    monkeypatch.setattr(
        "yt_subs.infrastructure.yt_dlp_adapter.YtDlpInspector",
        FakeInspector,
    )
    monkeypatch.setattr(cli, "run_batch_subtitle_job", lambda *args, **kwargs: _summary(tmp_path))

    result = CliRunner().invoke(
        app,
        [
            "batch",
            PLAYLIST_URL,
            "--remote-components",
            "ejs:npm",
            "--no-remote-components",
        ],
    )

    assert result.exit_code == 0
    assert captured["remote_components"] == ["ejs:npm"]
    assert captured["disable_remote_components"] is True


def test_batch_command_passes_network_stability_to_options_and_inspector(
    monkeypatch, tmp_path: Path
) -> None:
    captured = {}

    class FakeInspector:
        def __init__(self, **kwargs) -> None:
            captured["inspector"] = kwargs

        def inspect(self, url: str):
            return []

    def fake_batch(url: str, options, *, progress_callback=None, **kwargs):
        captured["options"] = {
            "force_ipv4": options.force_ipv4,
            "retries": options.retries,
            "extractor_retries": options.extractor_retries,
        }
        return _summary(tmp_path)

    monkeypatch.setattr(
        "yt_subs.infrastructure.yt_dlp_adapter.YtDlpInspector",
        FakeInspector,
    )
    monkeypatch.setattr(cli, "run_batch_subtitle_job", fake_batch)

    result = CliRunner().invoke(
        app,
        [
            "batch",
            PLAYLIST_URL,
            "--no-force-ipv4",
            "--retries",
            "4",
            "--extractor-retries",
            "6",
        ],
    )

    assert result.exit_code == 0
    assert captured["options"] == {
        "force_ipv4": False,
        "retries": 4,
        "extractor_retries": 6,
    }
    assert captured["inspector"]["force_ipv4"] is False
    assert captured["inspector"]["retries"] == 4
    assert captured["inspector"]["extractor_retries"] == 6
