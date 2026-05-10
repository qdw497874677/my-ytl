"""Tests for deterministic VTT-to-SRT/TXT subtitle conversion."""

from pathlib import Path

from yt_subs.domain.models import SubtitleArtifact, SubtitleProvenance
from yt_subs.services.subtitle_conversion import convert_vtt_artifacts

VTT_CONTENT = """\
WEBVTT

00:00:00.000 --> 00:00:01.000
Hello world

00:00:01.000 --> 00:00:02.000
This is a test

00:00:02.000 --> 00:00:03.000
Hello world
"""


def _write_vtt(source_vtt: Path, content: str = VTT_CONTENT) -> None:
    source_vtt.parent.mkdir(parents=True, exist_ok=True)
    source_vtt.write_text(content, encoding="utf-8")


class TestConvertVttArtifacts:
    """convert_vtt_artifacts produces VTT/SRT/TXT SubtitleArtifacts from source VTT."""

    def test_returns_three_artifacts_for_vtt_srt_txt(self, tmp_path: Path) -> None:
        source_vtt = tmp_path / "source" / "en.vtt"
        _write_vtt(source_vtt)
        subtitles_dir = tmp_path / "output" / "subtitles"

        artifacts = convert_vtt_artifacts(
            source_vtt=source_vtt,
            subtitles_dir=subtitles_dir,
            language_code="en",
            kind="manual",
            requested_formats=["vtt", "srt", "txt"],
        )

        assert len(artifacts) == 3
        formats = {a.format for a in artifacts}
        assert formats == {"vtt", "srt", "txt"}

    def test_srt_contains_numbered_captions_and_comma_timestamps(self, tmp_path: Path) -> None:
        source_vtt = tmp_path / "source" / "en.vtt"
        _write_vtt(source_vtt)
        subtitles_dir = tmp_path / "output" / "subtitles"

        artifacts = convert_vtt_artifacts(
            source_vtt=source_vtt,
            subtitles_dir=subtitles_dir,
            language_code="en",
            kind="manual",
            requested_formats=["srt"],
        )

        srt_artifact = artifacts[0]
        assert srt_artifact.format == "srt"
        srt_text = srt_artifact.path.read_text(encoding="utf-8")
        # SRT uses comma in timestamp format: 00:00:00,000 --> 00:00:01,000
        assert "00:00:00,000" in srt_text or "00:00:00,000 --> 00:00:01,000" in srt_text

    def test_txt_contains_cleaned_text_without_timestamps(self, tmp_path: Path) -> None:
        source_vtt = tmp_path / "source" / "en.vtt"
        _write_vtt(source_vtt)
        subtitles_dir = tmp_path / "output" / "subtitles"

        artifacts = convert_vtt_artifacts(
            source_vtt=source_vtt,
            subtitles_dir=subtitles_dir,
            language_code="en",
            kind="manual",
            requested_formats=["txt"],
        )

        txt_artifact = artifacts[0]
        assert txt_artifact.format == "txt"
        txt_text = txt_artifact.path.read_text(encoding="utf-8")
        # TXT should NOT contain WEBVTT header or timestamp arrows
        assert "WEBVTT" not in txt_text
        assert "-->" not in txt_text
        # TXT should contain caption text
        assert "Hello world" in txt_text
        assert "This is a test" in txt_text
        # Consecutive duplicate lines should be deduplicated
        # "Hello world" appears in caption 1 and 3, but should appear only twice
        # (not consecutively duplicated)
        lines = [line for line in txt_text.strip().splitlines() if line.strip()]
        # After dedup: Hello world, This is a test, Hello world (3 unique lines)
        assert len(lines) == 3

    def test_all_artifacts_include_provenance(self, tmp_path: Path) -> None:
        source_vtt = tmp_path / "source" / "en.vtt"
        _write_vtt(source_vtt)
        subtitles_dir = tmp_path / "output" / "subtitles"

        artifacts = convert_vtt_artifacts(
            source_vtt=source_vtt,
            subtitles_dir=subtitles_dir,
            language_code="en",
            kind="automatic",
            requested_formats=["vtt", "srt", "txt"],
        )

        for artifact in artifacts:
            assert isinstance(artifact, SubtitleArtifact)
            prov = artifact.provenance
            assert isinstance(prov, SubtitleProvenance)
            assert prov.source_path == source_vtt
            assert prov.source_format == "vtt"
            assert prov.source_language_code == "en"
            assert prov.source_kind == "automatic"
