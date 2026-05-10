"""Tests for Phase 2 subtitle artifact domain contracts."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from yt_subs.domain.models import (
    MissingSubtitle,
    SubtitleArtifact,
    SubtitleDownloadOptions,
    SubtitleFormat,
    SubtitleKind,
    SubtitleProvenance,
)


class TestSubtitleDownloadOptions:
    """SubtitleDownloadOptions preserves languages and formats."""

    def test_preserves_languages_and_formats(self, tmp_path: Path) -> None:
        opts = SubtitleDownloadOptions(
            output_dir=tmp_path,
            languages=["en", "ja"],
            formats=["vtt", "srt", "txt"],
        )
        assert opts.languages == ["en", "ja"]
        assert opts.formats == ["vtt", "srt", "txt"]

    def test_default_format_is_vtt(self, tmp_path: Path) -> None:
        opts = SubtitleDownloadOptions(output_dir=tmp_path, languages=["en"])
        assert opts.formats == ["vtt"]

    def test_invalid_format_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError):
            SubtitleDownloadOptions(
                output_dir=tmp_path,
                languages=["en"],
                formats=["pdf"],
            )


class TestSubtitleArtifact:
    """SubtitleArtifact requires language code, kind, format, path, provenance."""

    def test_valid_artifact(self, tmp_path: Path) -> None:
        provenance = SubtitleProvenance(
            source_path=tmp_path / "en.vtt",
            source_format="vtt",
            source_language_code="en",
            source_kind="manual",
        )
        artifact = SubtitleArtifact(
            language_code="en",
            kind="manual",
            format="srt",
            path=tmp_path / "en.manual.srt",
            provenance=provenance,
        )
        assert artifact.language_code == "en"
        assert artifact.kind == "manual"
        assert artifact.format == "srt"

    def test_missing_required_field_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError):
            SubtitleArtifact(
                language_code="en",
                kind="manual",
                format="vtt",
                # missing path and provenance
            )


class TestMissingSubtitle:
    """MissingSubtitle serializes to JSON-safe data."""

    def test_unavailable_reason(self) -> None:
        missing = MissingSubtitle(language_code="fr", reason="unavailable")
        assert missing.language_code == "fr"
        assert missing.reason == "unavailable"

    def test_with_detail(self) -> None:
        missing = MissingSubtitle(
            language_code="fr", reason="unavailable", detail="No French subtitles found"
        )
        data = missing.model_dump(mode="json")
        assert data["language_code"] == "fr"
        assert data["detail"] == "No French subtitles found"

    def test_json_serializable(self) -> None:
        missing = MissingSubtitle(language_code="fr", reason="unavailable")
        data = missing.model_dump(mode="json")
        assert isinstance(data, dict)
        assert "language_code" in data
        assert "reason" in data
