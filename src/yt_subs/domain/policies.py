"""Pure policies for stable output identities and artifact paths."""

import re
from pathlib import Path

from yt_subs.domain.models import InspectItem, JobOptions, OutputIdentity

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_title_fragment(title: str | None) -> str | None:
    if not title:
        return None
    normalized = _UNSAFE_CHARS.sub("-", title.strip()).strip("-._")
    return normalized[:48] or None


def build_output_identity(item: InspectItem, options: JobOptions) -> OutputIdentity:
    """Build a stable identity whose canonical key always includes the video ID."""

    title_fragment = _safe_title_fragment(item.title)
    item_key = item.video_id if title_fragment is None else f"{item.video_id}-{title_fragment}"
    bundle_dir = options.output_dir / "items" / item_key
    return OutputIdentity(
        video_id=item.video_id,
        item_key=item_key,
        title=item.title,
        bundle_dir=bundle_dir,
        metadata_path=bundle_dir / "metadata" / "item.json",
        subtitles_dir=bundle_dir / "subtitles",
        logs_dir=bundle_dir / "logs",
        media_dir=bundle_dir / "media",
    )


def plan_item_paths(identity: OutputIdentity, options: JobOptions) -> OutputIdentity:
    """Plan deterministic artifact paths under the selected output root."""

    bundle_dir = Path(options.output_dir) / "items" / identity.item_key
    return OutputIdentity(
        video_id=identity.video_id,
        item_key=identity.item_key,
        title=identity.title,
        bundle_dir=bundle_dir,
        metadata_path=bundle_dir / "metadata" / "item.json",
        subtitles_dir=bundle_dir / "subtitles",
        logs_dir=bundle_dir / "logs",
        media_dir=bundle_dir / "media",
    )
