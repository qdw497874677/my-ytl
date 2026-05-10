"""Deterministic VTT-to-SRT/TXT subtitle conversion with provenance."""

import shutil
from pathlib import Path

import webvtt

from yt_subs.domain.models import (
    SubtitleArtifact,
    SubtitleFormat,
    SubtitleKind,
    SubtitleProvenance,
)


def convert_vtt_artifacts(
    source_vtt: Path,
    subtitles_dir: Path,
    language_code: str,
    kind: SubtitleKind,
    requested_formats: list[SubtitleFormat],
) -> list[SubtitleArtifact]:
    """Convert a source VTT file into requested subtitle formats under subtitles_dir.

    Returns one SubtitleArtifact per requested format with provenance
    pointing to the source VTT.
    """
    subtitles_dir.mkdir(parents=True, exist_ok=True)
    provenance = SubtitleProvenance(
        source_path=source_vtt,
        source_format="vtt",
        source_language_code=language_code,
        source_kind=kind,
    )
    artifacts: list[SubtitleArtifact] = []

    for fmt in requested_formats:
        if fmt == "vtt":
            dest = subtitles_dir / f"{language_code}.{kind}.vtt"
            if source_vtt.resolve() != dest.resolve():
                shutil.copy2(source_vtt, dest)
        elif fmt == "srt":
            dest = subtitles_dir / f"{language_code}.{kind}.srt"
            _convert_vtt_to_srt(source_vtt, dest)
        elif fmt == "txt":
            dest = subtitles_dir / f"{language_code}.{kind}.txt"
            _convert_vtt_to_txt(source_vtt, dest)

        artifacts.append(
            SubtitleArtifact(
                language_code=language_code,
                kind=kind,
                format=fmt,
                path=dest,
                provenance=provenance,
            )
        )

    return artifacts


def _convert_vtt_to_srt(source_vtt: Path, dest: Path) -> None:
    """Convert VTT to SRT using webvtt-py's built-in SRT writer."""
    vtt = webvtt.read(str(source_vtt))
    with open(dest, "w", encoding="utf-8") as handle:
        vtt.write(handle, format="srt")


def _convert_vtt_to_txt(source_vtt: Path, dest: Path) -> None:
    """Convert VTT to clean text: caption text only, no timestamps, deduplicated lines."""
    vtt = webvtt.read(str(source_vtt))
    lines: list[str] = []
    prev_line = ""

    for caption in vtt.captions:
        text = caption.text.strip()
        if not text:
            continue
        # Drop consecutive duplicates
        if text == prev_line:
            continue
        lines.append(text)
        prev_line = text

    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
