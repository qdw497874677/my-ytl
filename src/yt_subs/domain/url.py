"""Lightweight YouTube URL intake classification."""

from urllib.parse import parse_qs, urlparse

from pydantic import ValidationError

from yt_subs.domain.models import TargetRequest

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


def parse_target_url(url: str) -> TargetRequest:
    """Classify common YouTube target URLs while preserving the original URL."""

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host not in YOUTUBE_HOSTS:
        raise ValidationError.from_exception_data(
            "TargetRequest",
            [
                {
                    "type": "value_error",
                    "loc": ("url",),
                    "msg": "Unsupported URL host; expected a YouTube URL",
                    "input": url,
                    "ctx": {"error": ValueError("Unsupported URL host; expected a YouTube URL")},
                }
            ],
        )

    query = parse_qs(parsed.query)
    kind = "playlist" if query.get("list") else "video"
    return TargetRequest(url=url, kind=kind)
