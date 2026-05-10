"""Single-video subtitle download orchestration service."""

import json
from typing import Protocol

from yt_subs.domain.models import (
    InspectItem,
    JobOptions,
    MissingSubtitle,
    SubtitleArtifact,
    SubtitleDownloadOptions,
    SubtitleDownloadResult,
    SubtitleTrack,
    VideoMetadata,
)
from yt_subs.domain.policies import build_output_identity, plan_item_paths
from yt_subs.domain.url import parse_target_url
from yt_subs.infrastructure.yt_dlp_adapter import YtDlpInspector, YtDlpSubtitleDownloader
from yt_subs.services.subtitle_conversion import convert_vtt_artifacts


class InspectorProto(Protocol):
    def inspect(self, url: str) -> list[InspectItem]: ...


class DownloaderProto(Protocol):
    def download_subtitles(
        self, url: str, subtitles_dir, languages: list[str], include_automatic: bool = True
    ) -> list: ...


def download_subtitles(
    url: str,
    options: SubtitleDownloadOptions,
    *,
    inspector: InspectorProto | None = None,
    downloader: DownloaderProto | None = None,
    cookies_from_browser: str | None = None,
    cookies_file: str | None = None,
) -> SubtitleDownloadResult:
    """Download subtitles for a single YouTube video and persist artifacts + metadata."""

    # Parse and inspect
    parse_target_url(url)
    inspector = inspector or YtDlpInspector(
        cookies_from_browser=cookies_from_browser, cookies_file=cookies_file
    )
    items = inspector.inspect(url)

    if len(items) != 1:
        msg = f"Expected exactly one video item, got {len(items)}"
        raise ValueError(msg)

    item = items[0]

    # Build output identity
    job_opts = JobOptions(output_dir=options.output_dir)
    identity = build_output_identity(item, job_opts)
    identity = plan_item_paths(identity, job_opts)

    # Resolve requested languages vs available tracks
    available_by_lang = _resolve_available_tracks(item.subtitles, options)

    # Determine missing languages
    missing_subtitles: list[MissingSubtitle] = []
    for lang in options.languages:
        if lang not in available_by_lang:
            missing_subtitles.append(MissingSubtitle(language_code=lang, reason="unavailable"))

    # Download VTT source files for available languages
    downloader = downloader or YtDlpSubtitleDownloader(
        cookies_from_browser=cookies_from_browser, cookies_file=cookies_file
    )
    available_langs = list(available_by_lang.keys())
    vtt_paths: list = []
    if available_langs:
        vtt_paths = downloader.download_subtitles(
            url, identity.subtitles_dir, available_langs, options.include_automatic
        )

    # Convert VTTs to requested formats
    all_artifacts: list[SubtitleArtifact] = []
    for vtt_path in vtt_paths:
        lang = _parse_language_from_vtt(vtt_path)
        track = available_by_lang.get(lang)
        if track is None:
            continue
        artifacts = convert_vtt_artifacts(
            source_vtt=vtt_path,
            subtitles_dir=identity.subtitles_dir,
            language_code=lang,
            kind=track.kind,
            requested_formats=list(options.formats),
        )
        all_artifacts.extend(artifacts)

    # Persist metadata
    identity.metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = VideoMetadata(
        video_id=item.video_id,
        title=item.title,
        webpage_url=item.webpage_url,
        requested_languages=list(options.languages),
        requested_formats=list(options.formats),
        include_automatic=options.include_automatic,
        artifacts=all_artifacts,
        missing_languages=missing_subtitles,
    )
    identity.metadata_path.write_text(
        json.dumps(metadata.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return SubtitleDownloadResult(
        item=item,
        identity=identity,
        artifacts=all_artifacts,
        missing_subtitles=missing_subtitles,
        metadata_path=identity.metadata_path,
    )


def _resolve_available_tracks(
    tracks: list[SubtitleTrack], options: SubtitleDownloadOptions
) -> dict[str, SubtitleTrack]:
    """Build a map of language_code -> best available track, preferring manual."""
    available: dict[str, SubtitleTrack] = {}
    requested_set = set(options.languages)

    for track in tracks:
        if track.language_code not in requested_set:
            continue
        if track.kind == "automatic" and not options.include_automatic:
            continue
        existing = available.get(track.language_code)
        # Prefer manual over automatic
        if existing is None or (track.kind == "manual" and existing.kind == "automatic"):
            available[track.language_code] = track

    return available


def _parse_language_from_vtt(vtt_path) -> str:
    """Extract language code from a VTT filename.

    Handles patterns like 'abc123.en.vtt', 'en.manual.vtt', 'en.vtt'.
    """
    stem = vtt_path.stem
    parts = stem.split(".")
    # Filter out known non-language parts
    skip = {"manual", "automatic"}
    for part in reversed(parts):
        if part not in skip and len(part) <= 10:
            return part
    return parts[0]
