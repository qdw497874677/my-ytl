from pathlib import Path

from typer.testing import CliRunner

from yt_subs.domain.models import InspectItem, JobOptions, OutputIdentity, SubtitleTrack
from yt_subs.interfaces import cli
from yt_subs.interfaces.cli import app
from yt_subs.services.inspect import InspectedPlanItem, InspectReport

YOUTUBE_URL = "https://www.youtube.com/watch?v=abc123"


def _report(tmp_path: Path) -> InspectReport:
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
    return InspectReport(
        target={"url": YOUTUBE_URL, "kind": "video"},
        items=[
            InspectedPlanItem(
                item=InspectItem(
                    video_id="abc123",
                    title="Example",
                    webpage_url=YOUTUBE_URL,
                    subtitles=[
                        SubtitleTrack(language_code="en", kind="manual", source_format="vtt"),
                        SubtitleTrack(language_code="ja", kind="automatic", source_format="vtt"),
                    ],
                ),
                identity=identity,
            )
        ],
    )


def test_inspect_command_calls_service_with_output_dir(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    def fake_inspect_target(url: str, options: JobOptions) -> InspectReport:
        captured["url"] = url
        captured["output_dir"] = options.output_dir
        return _report(tmp_path)

    monkeypatch.setattr(cli, "inspect_target", fake_inspect_target)

    result = CliRunner().invoke(app, ["inspect", YOUTUBE_URL, "--output-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert captured == {"url": YOUTUBE_URL, "output_dir": tmp_path}


def test_inspect_help_shows_examples_and_preview_purpose() -> None:
    result = CliRunner().invoke(app, ["inspect", "--help"])

    assert result.exit_code == 0
    assert "Examples" in result.output
    assert "preview" in result.output.lower()


def test_invalid_url_validation_is_user_facing() -> None:
    result = CliRunner().invoke(app, ["inspect", "https://example.com/watch?v=abc"])

    assert result.exit_code != 0
    assert "Unsupported URL" in result.output


def test_inspect_output_includes_video_id_and_planned_bundle(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cli, "inspect_target", lambda url, options: _report(tmp_path))

    result = CliRunner().invoke(app, ["inspect", YOUTUBE_URL, "--output-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert "abc123" in result.output
    assert str(tmp_path / "items" / "abc123-Example") in result.output


def test_inspect_output_includes_subtitle_languages_and_kinds(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cli, "inspect_target", lambda url, options: _report(tmp_path))

    result = CliRunner().invoke(app, ["inspect", YOUTUBE_URL, "--output-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert "en (manual)" in result.output
    assert "ja (automatic)" in result.output


def test_playlist_inspect_output_includes_multiple_items(monkeypatch, tmp_path: Path) -> None:
    base = _report(tmp_path)
    second_identity = base.items[0].identity.model_copy(
        update={
            "video_id": "def456",
            "item_key": "def456-Second",
            "bundle_dir": tmp_path / "items" / "def456-Second",
        }
    )
    report = base.model_copy(
        update={
            "items": [
                base.items[0],
                InspectedPlanItem(
                    item=base.items[0].item.model_copy(
                        update={"video_id": "def456", "title": "Second", "playlist_index": 2}
                    ),
                    identity=second_identity,
                ),
            ]
        }
    )
    monkeypatch.setattr(cli, "inspect_target", lambda url, options: report)

    result = CliRunner().invoke(app, ["inspect", YOUTUBE_URL, "--output-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert "abc123" in result.output
    assert "def456" in result.output
