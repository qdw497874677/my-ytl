"""Tests for the subtitle download CLI command."""

from pathlib import Path

from typer.testing import CliRunner

from yt_subs.domain.models import (
    InspectItem,
    MissingSubtitle,
    OutputIdentity,
    SubtitleArtifact,
    SubtitleDownloadResult,
    SubtitleProvenance,
)
from yt_subs.interfaces import cli
from yt_subs.interfaces.cli import app

YOUTUBE_URL = "https://www.youtube.com/watch?v=abc123"


def _make_result(tmp_path: Path) -> SubtitleDownloadResult:
    identity = OutputIdentity(
        video_id="abc123",
        item_key="abc123-Example",
        title="Example",
        bundle_dir=tmp_path / "items" / "abc123-Example",
        metadata_path=tmp_path / "items" / "abc123-Example" / "metadata" / "item.json",
        subtitles_dir=tmp_path / "items" / "abc123-Example" / "subtitles",
        logs_dir=tmp_path / "items" / "abc123-Example" / "logs",
        media_dir=tmp_path / "items" / "abc123-Example" / "media",
    )
    provenance = SubtitleProvenance(
        source_path=tmp_path / "en.vtt",
        source_format="vtt",
        source_language_code="en",
        source_kind="manual",
    )
    return SubtitleDownloadResult(
        item=InspectItem(
            video_id="abc123",
            title="Example",
            webpage_url=YOUTUBE_URL,
        ),
        identity=identity,
        artifacts=[
            SubtitleArtifact(
                language_code="en",
                kind="manual",
                format="vtt",
                path=identity.subtitles_dir / "en.manual.vtt",
                provenance=provenance,
            ),
            SubtitleArtifact(
                language_code="ja",
                kind="automatic",
                format="srt",
                path=identity.subtitles_dir / "ja.automatic.srt",
                provenance=SubtitleProvenance(
                    source_path=tmp_path / "ja.vtt",
                    source_format="vtt",
                    source_language_code="ja",
                    source_kind="automatic",
                ),
            ),
        ],
        missing_subtitles=[
            MissingSubtitle(language_code="fr", reason="unavailable"),
        ],
        metadata_path=identity.metadata_path,
    )


def test_download_command_calls_service_with_languages_and_formats(
    monkeypatch, tmp_path: Path
) -> None:
    captured = {}
    result_data = _make_result(tmp_path)

    def fake_download(url: str, options, *, inspector=None, downloader=None):
        captured["url"] = url
        captured["languages"] = options.languages
        captured["formats"] = options.formats
        captured["output_dir"] = options.output_dir
        return result_data

    monkeypatch.setattr(cli, "download_subtitles", fake_download)

    result = CliRunner().invoke(
        app,
        [
            "download",
            YOUTUBE_URL,
            "--language",
            "en",
            "--language",
            "ja",
            "--format",
            "vtt",
            "--format",
            "txt",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert captured["languages"] == ["en", "ja"]
    assert captured["formats"] == ["vtt", "txt"]
    assert captured["output_dir"] == tmp_path


def test_download_output_includes_artifact_paths_and_metadata(monkeypatch, tmp_path: Path) -> None:
    result_data = _make_result(tmp_path)
    monkeypatch.setattr(
        cli,
        "download_subtitles",
        lambda url, options, **kw: result_data,
    )

    result = CliRunner().invoke(
        app, ["download", YOUTUBE_URL, "--language", "en", "--output-dir", str(tmp_path)]
    )

    assert result.exit_code == 0
    assert "metadata/item.json" in result.output


def test_download_output_shows_missing_language_unavailable(monkeypatch, tmp_path: Path) -> None:
    result_data = _make_result(tmp_path)
    monkeypatch.setattr(
        cli,
        "download_subtitles",
        lambda url, options, **kw: result_data,
    )

    result = CliRunner().invoke(
        app, ["download", YOUTUBE_URL, "--language", "en", "--output-dir", str(tmp_path)]
    )

    assert result.exit_code == 0
    assert "fr" in result.output
    assert "unavailable" in result.output


def test_download_help_includes_language_format_and_examples() -> None:
    result = CliRunner().invoke(app, ["download", "--help"])

    assert result.exit_code == 0
    assert "--language" in result.output
    assert "--format" in result.output
