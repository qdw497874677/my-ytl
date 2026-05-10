"""Isolated yt-dlp metadata inspection adapter."""

from collections.abc import Iterable
from typing import Any

from yt_dlp import YoutubeDL

from yt_subs.domain.models import InspectItem, SubtitleTrack


class YtDlpInspector:
    """Adapter boundary for metadata-only yt-dlp inspection."""

    def __init__(self, ydl_options: dict[str, Any] | None = None) -> None:
        self.ydl_options = {"ignoreconfig": True, "quiet": True, "skip_download": True}
        if ydl_options:
            self.ydl_options.update(ydl_options)

    def inspect(self, url: str) -> list[InspectItem]:
        with YoutubeDL(self.ydl_options) as ydl:
            raw_info = ydl.extract_info(url, download=False)
            if hasattr(ydl, "sanitize_info"):
                raw_info = ydl.sanitize_info(raw_info)
        return list(_normalize_info(raw_info))


def _normalize_info(raw_info: dict[str, Any]) -> Iterable[InspectItem]:
    entries = raw_info.get("entries")
    if entries:
        for index, entry in enumerate(entries, start=1):
            if entry:
                yield _normalize_item(entry, playlist_index=index)
        return
    yield _normalize_item(raw_info, playlist_index=raw_info.get("playlist_index"))


def _normalize_item(info: dict[str, Any], playlist_index: int | None = None) -> InspectItem:
    return InspectItem(
        video_id=str(info.get("id") or info.get("display_id")),
        title=info.get("title"),
        webpage_url=info.get("webpage_url") or info.get("original_url"),
        playlist_index=playlist_index,
        subtitles=[
            *_tracks(info.get("subtitles") or {}, "manual"),
            *_tracks(info.get("automatic_captions") or {}, "automatic"),
        ],
    )


def _tracks(raw_tracks: dict[str, list[dict[str, Any]]], kind: str) -> list[SubtitleTrack]:
    tracks: list[SubtitleTrack] = []
    for language_code, variants in raw_tracks.items():
        first = variants[0] if variants else {}
        tracks.append(
            SubtitleTrack(
                language_code=language_code,
                language_name=first.get("name"),
                kind=kind,
                source_format=first.get("ext"),
            )
        )
    return tracks
