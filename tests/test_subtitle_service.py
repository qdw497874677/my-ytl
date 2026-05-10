"""Tests for single-video subtitle download orchestration service."""

import json
from pathlib import Path

from yt_subs.domain.models import (
    InspectItem,
    SubtitleDownloadOptions,
    SubtitleTrack,
)
from yt_subs.services.subtitles import download_subtitles


class FakeInspector:
    def __init__(self, items: list[InspectItem]) -> None:
        self._items = items

    def inspect(self, url: str) -> list[InspectItem]:
        return self._items


class FakeDownloader:
    def __init__(self, vtt_files: list[Path] | None = None) -> None:
        self._vtt_files = vtt_files or []
        self.download_calls: list[tuple] = []

    def download_subtitles(
        self, url: str, subtitles_dir: Path, languages: list[str], include_automatic: bool = True
    ) -> list[Path]:
        self.download_calls.append((url, subtitles_dir, languages, include_automatic))
        # Write dummy VTT files for each requested language
        subtitles_dir.mkdir(parents=True, exist_ok=True)
        written = []
        for lang in languages:
            vtt_path = subtitles_dir / f"{lang}.manual.vtt"
            vtt_path.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nTest\n", encoding="utf-8")
            written.append(vtt_path)
        return written


def _make_item(
    video_id: str = "abc123",
    title: str = "Test video",
    url: str = "https://www.youtube.com/watch?v=abc123",
    subtitles: list[SubtitleTrack] | None = None,
) -> InspectItem:
    return InspectItem(
        video_id=video_id,
        title=title,
        webpage_url=url,
        subtitles=subtitles or [],
    )


class TestDownloadSubtitles:
    def test_returns_artifacts_for_both_languages(self, tmp_path: Path) -> None:
        item = _make_item(
            subtitles=[
                SubtitleTrack(language_code="en", kind="manual", source_format="vtt"),
                SubtitleTrack(language_code="ja", kind="automatic", source_format="vtt"),
            ]
        )
        opts = SubtitleDownloadOptions(output_dir=tmp_path, languages=["en", "ja"], formats=["vtt"])

        result = download_subtitles(
            "https://www.youtube.com/watch?v=abc123",
            opts,
            inspector=FakeInspector([item]),
            downloader=FakeDownloader(),
        )

        lang_codes = {a.language_code for a in result.artifacts}
        assert "en" in lang_codes
        assert "ja" in lang_codes

    def test_missing_language_reported_as_unavailable(self, tmp_path: Path) -> None:
        item = _make_item(
            subtitles=[
                SubtitleTrack(language_code="en", kind="manual", source_format="vtt"),
            ]
        )
        opts = SubtitleDownloadOptions(output_dir=tmp_path, languages=["en", "fr"], formats=["vtt"])

        result = download_subtitles(
            "https://www.youtube.com/watch?v=abc123",
            opts,
            inspector=FakeInspector([item]),
            downloader=FakeDownloader(),
        )

        missing_langs = {m.language_code for m in result.missing_subtitles}
        assert "fr" in missing_langs
        assert all(m.reason == "unavailable" for m in result.missing_subtitles)

    def test_metadata_json_written_with_artifacts(self, tmp_path: Path) -> None:
        item = _make_item(
            subtitles=[
                SubtitleTrack(language_code="en", kind="manual", source_format="vtt"),
            ]
        )
        opts = SubtitleDownloadOptions(output_dir=tmp_path, languages=["en"], formats=["vtt"])

        result = download_subtitles(
            "https://www.youtube.com/watch?v=abc123",
            opts,
            inspector=FakeInspector([item]),
            downloader=FakeDownloader(),
        )

        assert result.metadata_path.exists()
        metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
        assert metadata["video_id"] == "abc123"
        assert "en" in metadata["requested_languages"]
        assert len(metadata["artifacts"]) >= 1

    def test_manual_automatic_kind_preserved(self, tmp_path: Path) -> None:
        item = _make_item(
            subtitles=[
                SubtitleTrack(language_code="en", kind="manual", source_format="vtt"),
                SubtitleTrack(language_code="ja", kind="automatic", source_format="vtt"),
            ]
        )
        opts = SubtitleDownloadOptions(output_dir=tmp_path, languages=["en", "ja"], formats=["vtt"])

        result = download_subtitles(
            "https://www.youtube.com/watch?v=abc123",
            opts,
            inspector=FakeInspector([item]),
            downloader=FakeDownloader(),
        )

        kinds_by_lang = {a.language_code: a.kind for a in result.artifacts}
        assert kinds_by_lang["en"] == "manual"
        assert kinds_by_lang["ja"] == "automatic"

    def test_prefers_manual_when_both_exist(self, tmp_path: Path) -> None:
        """When a language has both manual and automatic tracks, prefer manual."""
        item = _make_item(
            subtitles=[
                SubtitleTrack(language_code="en", kind="manual", source_format="vtt"),
                SubtitleTrack(language_code="en", kind="automatic", source_format="vtt"),
            ]
        )
        opts = SubtitleDownloadOptions(output_dir=tmp_path, languages=["en"], formats=["vtt"])

        result = download_subtitles(
            "https://www.youtube.com/watch?v=abc123",
            opts,
            inspector=FakeInspector([item]),
            downloader=FakeDownloader(),
        )

        # Should only have one artifact for "en" (manual preferred)
        en_artifacts = [a for a in result.artifacts if a.language_code == "en"]
        assert len(en_artifacts) == 1
        assert en_artifacts[0].kind == "manual"
